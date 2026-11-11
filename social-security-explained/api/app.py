"""Social Security, Explained — no-account constituent finder.

Official data: House Clerk XML, Senate contact XML, Census Geocoder.
Each address is sent in an HTTPS POST body only to this service, then to Census.
No persistence, cookies, analytics, address logs, user data cache, or speculative matches.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import os
import json
import re
import threading
import time
from typing import Any
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool
from defusedxml.ElementTree import fromstring
from bs4 import BeautifulSoup

APP = FastAPI(title="Social Security Civic Finder", docs_url=None, redoc_url=None, openapi_url=None)
HOUSE_XML = "https://clerk.house.gov/xml/lists/MemberData.xml"
SENATE_XML = "https://www.senate.gov/general/contact_information/senators_cfm.xml"
CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/geographies/address"
HOUSE_DIRECTORY = "https://www.house.gov/representatives"
SENATE_DIRECTORY = "https://www.senate.gov/senators/contact/"
TRUSTED_ORIGINS = {
    "https://social-security-explained.onrender.com",
    "https://cal2020.github.io",
    "http://127.0.0.1:8000", "http://localhost:8000",
    "http://127.0.0.1:8765", "http://localhost:8765",
}
STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR AS GU MP VI".split())
NO_SENATORS = {"DC", "PR", "AS", "GU", "MP", "VI"}
HOUSE_ONE_SEAT = {"AK", "DE", "ND", "SD", "VT", "WY", "DC", "PR", "AS", "GU", "MP", "VI"}
STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado",
    "CT":"Connecticut","DE":"Delaware","FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho",
    "IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana",
    "ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota",
    "MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada",
    "NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York",
    "NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon",
    "PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota",
    "TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia",
    "WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
    "DC":"District of Columbia","PR":"Puerto Rico","AS":"American Samoa","GU":"Guam",
    "MP":"Northern Mariana Islands","VI":"Virgin Islands",
}
CACHE_LOCK = threading.Lock()
CACHE: dict[str, Any] = {"snapshot": None, "until": 0.0, "fetched_at": None, "error": None}
CACHE_SECONDS = 4 * 3600
STALE_MAX_SECONDS = 36 * 3600
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "SocialSecurityExplained/1.2 (public civic education; official-source lookup)", "Accept": "application/xml,text/xml,application/json"})


def current_congress(at: datetime | None = None) -> int:
    now = at or datetime.now(timezone.utc)
    # The 119th Congress convened January 3, 2025; each Congress lasts two years.
    year = now.year if (now.month, now.day) >= (1, 3) else now.year - 1
    return 119 + (year - 2025) // 2


def _text(element: ET.Element, *paths: str) -> str:
    for path in paths:
        node = element.find(path)
        if node is not None and node.text and node.text.strip():
            return node.text.strip()
    return ""


def clean_official_url(url: str, chamber: str) -> str | None:
    """Return only HTTPS addresses to an official House/Senate host."""
    if not url:
        return None
    u = urlsplit(url.strip())
    host = (u.hostname or "").lower()
    expected = ".house.gov" if chamber == "house" else ".senate.gov"
    if u.scheme != "https" or not (host.endswith(expected) or host in {"www.house.gov" if chamber == "house" else "www.senate.gov"}):
        return None
    if u.username or u.password or u.port not in {None, 443}:
        return None
    return url.strip()


def parse_house(xml: bytes, expected_congress: int | None = None) -> dict[str, dict]:
    root = fromstring(xml)
    declared = _text(root, ".//title-info/congress-num")
    if expected_congress is not None and declared and declared.isdigit() and int(declared) != expected_congress:
        raise ValueError(f"House official roster is Congress {declared}; expected {expected_congress}")
    result: dict[str, dict] = {}
    for member in root.findall(".//members/member"):
        code = _text(member, "statedistrict")
        if not re.fullmatch(r"[A-Z]{2}\d{2}", code):
            continue
        state, district = code[:2], int(code[2:])
        if state not in STATES:
            continue
        info = member.find("member-info")
        if info is None:
            info = member
        full_name = _text(info, "official-name", "firstname")
        if not full_name:
            first, last = _text(info, "firstname"), _text(info, "lastname")
            full_name = f"{first} {last}".strip()
        if not full_name:
            continue
        bio = _text(info, "bioguideID")
        kind = "delegate" if state in NO_SENATORS else "representative"
        result[f"{state}-{district:02d}"] = {
            "name": full_name, "state": state, "district": district, "kind": kind,
            "bioguide": bio if re.fullmatch(r"[A-Za-z]\d{6}", bio) else None,
            "official_url": HOUSE_DIRECTORY,
            "official_url_kind": "directory",
            "phone": _text(info, "phone") or None,
        }
    return result


def parse_senate(xml: bytes) -> dict[str, list[dict]]:
    root = fromstring(xml)
    states: dict[str, list[dict]] = {}
    for m in root.findall(".//member"):
        state = _text(m, "state")
        if state not in STATES or state in NO_SENATORS:
            continue
        name = _text(m, "member_full", "full_name", "name")
        if not name:
            name = " ".join(filter(None, (_text(m, "first_name"), _text(m, "last_name"))))
        if "," in name:
            last, first = name.split(",", 1)
            name = f"{first.strip()} {last.strip()}".strip()
        if not name:
            continue
        link = clean_official_url(_text(m, "contact_form", "email", "website"), "senate")
        states.setdefault(state, []).append({
            "name": name, "state": state, "kind": "senator", "phone": _text(m, "phone") or None,
            "official_url": link or SENATE_DIRECTORY,
            "official_url_kind": "office" if link else "directory",
        })
    return states


def add_house_websites(html: bytes, roster: dict[str, dict]) -> int:
    """Enrich links only if House.gov independently identifies same state/district/name.

    A changing HTML layout never causes a guessed contact URL; fallback to official directory.
    """
    soup = BeautifulSoup(html, "html.parser")
    state_by_name = {v.casefold(): k for k, v in STATE_NAMES.items()}
    applied = 0
    for table in soup.find_all("table"):
        title = table.find_previous(["h2", "h3", "h4", "caption"])
        state = state_by_name.get(title.get_text(" ", strip=True).casefold()) if title else None
        if not state:
            continue
        for row in table.find_all("tr"):
            cols = row.find_all("td", recursive=False)
            if len(cols) < 2:
                continue
            raw = cols[0].get_text(" ", strip=True)
            if raw.lower().startswith(("at large", "at-large", "delegate", "resident")):
                number = 0
            else:
                m = re.match(r"^(\d{1,2})(?:st|nd|rd|th)?$", raw, flags=re.I)
                if not m:
                    continue
                number = int(m.group(1))
            rec = roster.get(f"{state}-{number:02d}")
            if not rec:
                continue
            link = cols[1].find("a", href=True)
            if not link:
                continue
            url = clean_official_url(link["href"], "house")
            if not url or url == HOUSE_DIRECTORY:
                continue
            # Cross-check surname; don't claim the contact website is verified otherwise.
            listed_last = link.get_text(" ", strip=True).split(",", 1)[0].strip().casefold()
            actual_last = rec["name"].split()[-1].strip(",.").casefold()
            if listed_last not in {actual_last, actual_last.replace("-", " ")}:
                continue
            rec["official_url"] = url
            rec["official_url_kind"] = "office"
            applied += 1
    return applied


def refresh_officials() -> tuple[dict, str | None, str]:
    """Only cache the public roster; never user addresses or requests."""
    now = time.time()
    with CACHE_LOCK:
        if CACHE["snapshot"] is not None and now < CACHE["until"]:
            return CACHE["snapshot"], CACHE["error"], CACHE["fetched_at"]
        try:
            house = HTTP.get(HOUSE_XML, timeout=(4, 12))
            house.raise_for_status()
            senate = HTTP.get(SENATE_XML, timeout=(4, 12))
            senate.raise_for_status()
            congress = current_congress()
            h = parse_house(house.content, congress)
            s = parse_senate(senate.content)
            if len(h) < 420 or sum(map(len, s.values())) < 95:
                raise ValueError("Official feeds incomplete; refusing to guess names")
            # Optional third official source for direct member-website links.
            try:
                page = HTTP.get(HOUSE_DIRECTORY, timeout=(3, 8))
                page.raise_for_status()
                add_house_websites(page.content, h)
            except Exception:
                pass  # House Clerk names remain valid; use House.gov directory fallback.
            snap = {"house": h, "senate": s, "congress": congress}
            CACHE.update(snapshot=snap, until=now + CACHE_SECONDS, fetched_at=datetime.now(timezone.utc).isoformat(), error=None)
            return snap, None, CACHE["fetched_at"]
        except Exception as exc:
            # Error is only a public-source status; do not log incoming addresses.
            if CACHE["snapshot"] is not None and now - (CACHE["until"] - CACHE_SECONDS) < STALE_MAX_SECONDS:
                CACHE["until"] = now + 300
                CACHE["error"] = "Live official roster temporarily unavailable; showing last confirmed roster, verify before sending."
                return CACHE["snapshot"], CACHE["error"], CACHE["fetched_at"]
            raise RuntimeError("Official congressional data could not be verified right now") from exc


def district_from_census(data: dict, state: str) -> int | None:
    matches = data.get("result", {}).get("addressMatches", [])
    if not matches or len(matches) > 8:
        raise ValueError("The Census Bureau could not match this address uniquely")
    found: set[int] = set()
    for m in matches:
        comps = m.get("addressComponents", {})
        if comps.get("state", "").upper() != state:
            raise ValueError("The Census matched a different state. Check your address")
        geos = m.get("geographies", {})
        if not isinstance(geos, dict):
            continue
        group = None
        for name, rows in geos.items():
            # 119th congressional geography in November 2026, 120th in Jan 2027.
            if f"{current_congress()}" in name and "Congressional" in name:
                group = rows
                break
        if not group:
            raise ValueError("Census did not return a current-Congress district; use House.gov instead")
        for g in group:
            key = f"CD{current_congress()}"
            raw = str(g.get(key) or g.get("BASENAME") or "")
            if re.fullmatch(r"\d{1,2}", raw):
                found.add(int(raw))
    if len(found) != 1:
        raise ValueError("The address matched multiple or unknown districts; verify on House.gov")
    return next(iter(found))


def get_census_district(street: str, city: str, state: str, zip_code: str) -> int:
    params = {"street": street, "city": city, "state": state,
              "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"}
    if zip_code:
        params["zip"] = zip_code
    r = HTTP.get(CENSUS_URL, params=params, timeout=(4, 14))
    r.raise_for_status()
    return district_from_census(r.json(), state)


def _valid(value: Any, max_chars: int, regex: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > max_chars or not re.fullmatch(regex, value):
        raise ValueError("Check the address fields and try again")
    return value.strip()


def api_error(message: str, code: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=code)


@APP.middleware("http")
async def finish(request: Request, call_next):
    # Never log or persist request bodies, address text, cookies or URLs with PII.
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Vary"] = "Origin"
    origin = request.headers.get("origin", "")
    if origin in TRUSTED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@APP.get("/health")
def health():
    return {"ok": True, "congress": current_congress(), "lookup_data": "official House Clerk and U.S. Senate", "addresses_saved": False}


@APP.get("/api/roster-status")
async def roster_status():
    try:
        roster, warning, checked_at = await run_in_threadpool(refresh_officials)
        return {"ok": True, "congress": roster["congress"], "house_members": len(roster["house"]),
                "senators": sum(len(v) for v in roster["senate"].values()),
                "checked_at": checked_at, "warning": warning, "personal_data_stored": False}
    except Exception:
        return api_error("Official roster unavailable or incomplete; no names were guessed.", 503)


@APP.options("/api/lookup")
def preflight():
    return Response(status_code=204)


@APP.post("/api/lookup")
async def lookup(request: Request):
    origin = request.headers.get("origin", "")
    if origin and origin not in TRUSTED_ORIGINS:
        return api_error("This browser origin is not authorized.", 403)
    body = await request.body()
    if len(body) > 4096:
        return api_error("The lookup request is too large.", 413)
    try:
        data = json.loads(body)
    except (TypeError, ValueError):
        return api_error("Send a JSON lookup request.", 400)
    if not isinstance(data, dict):
        return api_error("Send a JSON lookup request.", 400)
    try:
        state = _valid(data.get("state", ""), 2, r"[A-Za-z]{2}").upper()
        if state not in STATES:
            raise ValueError("Select your U.S. state or territory")
        street = _valid(data.get("street", ""), 110, r"[\w .,#'\-/]*")
        city = _valid(data.get("city", ""), 75, r"[\w .'-]*")
        zip_code = _valid(data.get("zip", ""), 5, r"\d{0,5}")
        if zip_code and len(zip_code) != 5:
            raise ValueError("ZIP code must contain five digits")
        if street and not (zip_code or city):
            raise ValueError("Add your city or ZIP code to match a street address")
        if street and not re.match(r"^\d+[\w -]*\s+", street):
            raise ValueError("Enter a street number and street name")
        roster, warning, fetched_at = await run_in_threadpool(refresh_officials)
        result: dict[str, Any] = {"state": state, "congress": roster["congress"],
                                  "updated_at": fetched_at, "senators": roster["senate"].get(state, []),
                                  "house": None, "house_status": "address_needed", "warning": warning,
                                  "privacy": "The address was used for this lookup only and was not saved by the application."}
        district = None
        if state in HOUSE_ONE_SEAT and not street:
            district = 0
        if street:
            try:
                district = await run_in_threadpool(get_census_district, street, city, state, zip_code)
                result["house_status"] = "district_matched"
            except Exception as exc:
                result["house_status"] = "census_unavailable"
                result["district_error"] = str(exc) if isinstance(exc, ValueError) else "Census lookup is unavailable right now. Use House.gov to confirm your district."
        if district is not None:
            key = f"{state}-{district:02d}"
            result["district"] = district
            if key in roster["house"]:
                result["house"] = roster["house"][key]
                result["house_status"] = "matched"
            else:
                result["house_status"] = "vacant_or_unverified"
        return result
    except ValueError as exc:
        return api_error(str(exc), 400)
    except RuntimeError:
        return api_error("Official congressional feeds are temporarily unavailable. Please use the House.gov and Senate.gov links below.", 503)
    except Exception:
        return api_error("Lookup could not be completed. Use the official congressional directories below.", 502)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(APP, host="127.0.0.1", port=int(os.environ.get("PORT", "8766")))