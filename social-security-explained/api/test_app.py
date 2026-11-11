import importlib.util
import pathlib
import sys
from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(pathlib.Path(__file__).parent))
import app

HOUSE = b'''<MemberData publish-date="2026-11-11"><title-info><congress-num>119</congress-num></title-info><members>
<member><statedistrict>CA04</statedistrict><member-info><official-name>Mike Thompson</official-name><lastname>Thompson</lastname><firstname>Mike</firstname><bioguideID>T000000</bioguideID><phone>(202) 225-3311</phone></member-info></member>
<member><statedistrict>AK00</statedistrict><member-info><official-name>Nick Begich</official-name><lastname>Begich</lastname><firstname>Nick</firstname></member-info></member>
<member><statedistrict>DC00</statedistrict><member-info><official-name>Eleanor Norton</official-name><lastname>Norton</lastname><firstname>Eleanor</firstname></member-info></member>
</members></MemberData>'''
SENATE = b'''<contact_information>
<member><member_full>Schiff, Adam</member_full><state>CA</state><email>https://www.schiff.senate.gov/contact/</email><phone>202-224-3841</phone></member>
<member><member_full>Padilla, Alex</member_full><state>CA</state><website>https://www.padilla.senate.gov</website></member>
<member><member_full>Murkowski, Lisa</member_full><state>AK</state><website>https://www.murkowski.senate.gov</website></member>
<member><member_full>Sullivan, Dan</member_full><state>AK</state><website>https://www.sullivan.senate.gov</website></member>
</contact_information>'''
CENSUS = {"result":{"addressMatches":[{"addressComponents":{"state":"CA"},"geographies":{"119th Congressional Districts":[{"CD119":"04","GEOID":"0604"}]}}]}}
SNAPSHOT={"house":app.parse_house(HOUSE,119),"senate":app.parse_senate(SENATE),"congress":119}

@pytest.fixture
def client():
    with patch.object(app,"refresh_officials",return_value=(SNAPSHOT,None,"2026-11-11T16:00:00+00:00")),patch.object(app,"get_census_district",return_value=4):
        yield TestClient(app.APP)


def test_house_clerk_and_senate_parsers():
    h=app.parse_house(HOUSE,119)
    assert h["CA-04"]["name"]=="Mike Thompson"
    assert h["DC-00"]["kind"]=="delegate"
    assert h["CA-04"]["official_url_kind"]=="directory"
    s=app.parse_senate(SENATE)
    assert len(s["CA"])==2
    assert s["CA"][0]["official_url"].endswith("/contact/")
    assert s["CA"][0]["name"]=="Adam Schiff"


def test_actual_clerk_member_info_names():
    xml = b'''<MemberData><title-info><congress-num>119</congress-num></title-info><members><member><statedistrict>CO02</statedistrict><member-info><namelist>Neguse, Joe</namelist><firstname>Joe</firstname><lastname>Neguse</lastname></member-info></member></members></MemberData>'''
    assert app.parse_house(xml,119)["CO-02"]["name"] == "Joe Neguse"


def test_wrong_congress_fails_closed():
    with pytest.raises(ValueError):app.parse_house(HOUSE,120)


def test_house_link_enrichment_requires_state_district_and_surname():
    html=b'''<h2>California</h2><table><tr><th>District</th><th>Name</th></tr><tr><td>4th</td><td><a href="https://mikethompson.house.gov/">Thompson, Mike</a></td></tr><tr><td>5th</td><td><a href="https://wrong.house.gov/">Smith, Demo</a></td></tr></table>'''
    d=app.parse_house(HOUSE,119)
    assert app.add_house_websites(html,d)==1
    assert d["CA-04"]["official_url"]=="https://mikethompson.house.gov/"
    assert app.clean_official_url("https://evil.example/?x=house.gov","house") is None
    assert app.clean_official_url("https://evil.house.gov.attacker.test","house") is None
    assert app.clean_official_url("http://real.house.gov","house") is None


def test_census_distinguishes_current_from_future_and_mismatch():
    assert app.district_from_census(CENSUS,"CA")==4
    with pytest.raises(ValueError):app.district_from_census(CENSUS,"NV")
    future={"result":{"addressMatches":[{"addressComponents":{"state":"CA"},"geographies":{"120th Congressional Districts":[{"CD120":"11"}]}}]}}
    with pytest.raises(ValueError):app.district_from_census(future,"CA")
    mixed={"result":{"addressMatches":[{"addressComponents":{"state":"CA"},"geographies":{"119th Congressional Districts":[{"CD119":"04"},{"CD119":"05"}]}}]}}
    with pytest.raises(ValueError):app.district_from_census(mixed,"CA")


def test_current_congress_changes_in_january():
    assert app.current_congress(datetime(2026,11,11,tzinfo=timezone.utc))==119
    assert app.current_congress(datetime(2027,1,3,tzinfo=timezone.utc))==120


def test_state_only_returns_senators_without_guessing_house(client):
    r=client.post("/api/lookup",json={"state":"CA","zip":"94510"},headers={"Origin":"https://cal2020.github.io"})
    assert r.status_code==200
    assert r.json()["house"] is None
    assert r.json()["house_status"]=="address_needed"
    assert len(r.json()["senators"])==2
    assert r.headers["cache-control"].startswith("no-store")
    assert r.headers["access-control-allow-origin"]=="https://cal2020.github.io"


def test_address_returns_current_house_and_senate(client):
    r=client.post("/api/lookup",json={"state":"CA","zip":"94510","city":"Vallejo","street":"123 Example St"})
    assert r.status_code==200
    assert r.json()["district"]==4
    assert r.json()["house"]["name"]=="Mike Thompson"
    assert r.json()["house_status"]=="matched"
    assert "street" not in str(r.json()).lower()


def test_dc_returns_house_delegate_without_senators(client):
    r=client.post("/api/lookup",json={"state":"DC","zip":"20001"})
    assert r.status_code==200
    assert r.json()["house"]["kind"]=="delegate"
    assert r.json()["senators"]==[]


def test_alaska_at_large_house_and_senators(client):
    r=client.post("/api/lookup",json={"state":"AK"})
    assert r.json()["house"]["name"]=="Nick Begich"
    assert len(r.json()["senators"])==2


def test_address_error_fails_to_house_directory_but_not_senators(client):
    with patch.object(app,"get_census_district",side_effect=ValueError("Multiple districts")):
        r=client.post("/api/lookup",json={"state":"CA","street":"123 Example St","city":"Vallejo"})
    assert r.json()["house"] is None
    assert r.json()["house_status"]=="census_unavailable"
    assert len(r.json()["senators"])==2


def test_do_not_guess_vacant_seat(client):
    with patch.object(app,"get_census_district",return_value=5):
        r=client.post("/api/lookup",json={"state":"CA","street":"123 Example St","city":"Vallejo"})
    assert r.json()["house"] is None and r.json()["house_status"]=="vacant_or_unverified"


def test_untrusted_origin_and_no_sensitive_storage(client):
    r=client.post("/api/lookup",json={"state":"CA"},headers={"Origin":"https://phishing.example"})
    assert r.status_code==403
    assert "Access-Control-Allow-Origin" not in r.headers
    assert app.CACHE.get("address") is None


def test_malformed_requests(client):
    for data in [{"state":"CA","zip":"123"},{"state":"XX"},{"state":"CA","street":"Private Rd"},{"state":"CA","street":"123 Example St"}]:
        assert client.post("/api/lookup",json=data).status_code==400
    assert client.post("/api/lookup",data="bad",headers={"Content-Type":"application/json"}).status_code==400


def test_not_available_returns_503():
    with patch.object(app,"refresh_officials",side_effect=RuntimeError("cannot access XML")):
        r=TestClient(app.APP).post("/api/lookup",json={"state":"CA"})
    assert r.status_code==503 and "official" in r.json()["error"].lower()