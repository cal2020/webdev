# Automatic congressional representative finder — v1.2

The **Social Security, Explained** app includes a consent-based finder for the **currently serving** Congress. It is nonpartisan and designed to fail safely when official records are incomplete. The base explainer and calculators remain fully static and work without this API.

## User workflow

1. Pick a **state**. Optionally enter a five-digit ZIP (not enough to identify every House district). Click **Find my current lawmakers** to see the state's current U.S. senators from the official U.S. Senate XML feed. For at-large states and territories, the House Clerk XML may also identify the single delegate/representative without a street address.
2. For a district-specific House member, enter a **street number and street name** plus city or ZIP. Read and select the consent checkbox. Click Find to let the backend query the **U.S. Census Geocoder** for the 119th Congressional Districts while the 119th Congress is seated.
3. See matched currently serving officials, their office website or official directory, and a source-check date. Click **Use for my letter** to fill the existing letter-recipient fields, refresh the letter, and scroll to the editor.
4. Review/edit the letter. A visitor must still open the member's official contact form and **submit it themselves**. No outbound messages are sent by this application.

## Verified sources

- House Clerk: `https://clerk.house.gov/xml/lists/MemberData.xml` (membership, seat, name, BioGuide ID; current Congress only)
- House.gov: `https://www.house.gov/representatives` (member website enrichment, only if state/district/surname independently align)
- Senate: `https://www.senate.gov/general/contact_information/senators_cfm.xml` (names, states, contact links)
- Census Geocoder: `https://geocoding.geo.census.gov/geocoder/geographies/address`, benchmark `Public_AR_Current`, geography `Current_Current`. The API is called from the backend, **not** via browser JSONP.

The data parser rejects official feeds with implausibly few members, refuses to match Census geography for a different Congress, checks the Census-matched state, rejects multiple districts and mismatched/vacant seats, and permits HTTPS links only to `.house.gov` or `.senate.gov`. Officials who won an election but have not been sworn in are **not** treated as current representatives. This program will need a new-Congress review in January 2027.

## Privacy and uptime

- No cookies, localStorage, analytics, sign-in, address database or user-specific caches.
- **Only when the visitor clicks Find** does the browser send a POST body to the dedicated free Render API. A full address is submitted only after explicit consent.
- The backend sends the address to Census using its HTTPS API, and keeps only public official roster data in a four-hour in-memory cache. The hosting provider and Census **may** retain infrastructure logs. Claims of zero third-party logging would be inaccurate.
- No address is added to the browser URL or sent to GitHub Pages. Responses are marked `Cache-Control: no-store`.
- Cold starts and federal-site outages can delay lookup. The browser shows a timeout/error and direct House.gov/Senate.gov fallback links instead of guessing.
- No private addresses are included in tests or screenshots. Fixtures intentionally use fictional/example addresses.

## Local development and tests

```sh
python -m pip install -r social-security-explained/api/requirements.txt
python -m pytest -q social-security-explained/api/test_app.py
uvicorn app:APP --app-dir social-security-explained/api --host 127.0.0.1 --port 8766
```

Open the static app in a local HTTP server for the finder script. The explainer calculations do not require the API.

The API's `/health` endpoint checks process availability; `/api/roster-status` checks live official source access and publishes only public member counts / timestamps (no user input). 

## Limitations

A five-digit ZIP can contain multiple districts. Even a geocoded street address may be unmatched, stale after redistricting, or corrected in House.gov before Census data catches up. In those cases the page says **unverified** and uses official contact links. Contact pages may require the visitor's full constituent address. The system does not guarantee successful message delivery, does not create a combined-policy fiscal score, and does not keep a personal profile.

The optional federal-source backend is independently deployed and may sleep on the free plan. Public-source, public-URL and iOS Safari end-to-end checks should be recorded separately from local mocked-data tests.