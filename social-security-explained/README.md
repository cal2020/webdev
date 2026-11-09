# Social Security, Explained

**Your future. The facts. Your voice.** A dependency-free, accessible, responsive civic explainer about the 2026 Social Security Trustees Report, with interactive scenarios and a nonpartisan constituent-letter writer.

## Get started

**Fastest:** Open `Social-Security-Explained.html`, the self-contained version included in this release, directly in a modern browser. It has the CSS and JavaScript built in; no server, installation, API key, login, or internet connection is required for the educational features. Links to official government websites require an internet connection.

**To develop locally:** Open the modular `index.source.html` or start a local static file server in this folder:

```bash
python3 -m http.server 8000
```

Visit `http://localhost:8000`.

**To publish with GitHub Pages:** The deployed `index.html` is fully self-contained. Use that file for the public static URL. For modular development, `index.source.html`, `app.js`, and `styles.css` provide the matching editable source. Any static hosting service works. No framework or build command is required.

## What visitors can do

1. **See the real funding gap** — switch between 2032 retirement-and-survivor funding (78% payable) and 2034 *hypothetical combined-fund* financing (83% payable). The 2034 view requires a change in law, as the funds are separate.
2. **Explore their own dollar scenario** — enter estimated total household gross monthly benefits, use SSA's January 2026 average-benefit presets, and see monthly/annual funding-gap illustrations (22%, 17%, or no reduction). This is not an individual benefit estimate or a legislated cut.
3. **Compare six independently scored reform proposals** — see standalone actuarial effectiveness (the percent of the combined program's 75-year shortfall closed) and affected groups. Tax proposals include an illustrative *employee-share* impact at a user-entered wage, holding the 2026 wage cap fixed for comparison only.
4. **Contact Congress without a political agenda built in** — select one of the 50 states, D.C., or a U.S. territory and enter a ZIP; open live official Senate state pages (for states) or House.gov's representative/delegate directory, and prepare an editable letter from four nonpartisan approaches. Copy and download are performed locally in the browser. No email is sent automatically.
5. **Open the primary sources** — official SSA, House, Senate, and congressional research material are linked directly.

## Why certain functions are intentionally limited

- **No automatic legislator name matching by ZIP:** A ZIP code can span multiple House districts. The official House.gov tool can resolve the currently serving representative and request clarification if necessary. Senate.gov state pages identify the *current* senators rather than relying on stale hardcoded officeholder lists. For D.C. and U.S. territories, the app explains there are no U.S. senators and directs visitors to the official House delegate/resident commissioner listing. The House's current-Congress boundaries may differ from new post-election districts until January 2027.
- **No auto-submission to Congress:** Lawmakers use different contact forms, many with address verification or anti-abuse protections. The tool opens official contact pages and gives the visitor a prepared letter to submit personally.
- **No invented actuarial forecast:** Each proposed reform is independently scored under the 2026 SSA model. Scores should not be added together or treated as directly reducing the 2032 funding gap.
- **No storage/tracking:** This app has no cookies, analytics, localStorage, backend, or network requests. Any letter and location inputs stay in the current browser page, except when the visitor chooses to copy or download them. Visiting official government links is subject to those sites' own privacy policies.

## Data, official sources, and refresh policy

**Baseline:** Social Security Trustees Report published June 9, 2026, with intermediate assumptions. Data verified November 8, 2026.

- [SSA 2026 Trustees press release](https://www.ssa.gov/news/en/press/releases/2026-06-09.html)
- [SSA 2026 Trustees report: highlights](https://www.ssa.gov/oact/TR/2026/II_A_highlights.html)
- [SSA Office of the Chief Actuary: solvency provisions](https://www.ssa.gov/OACT/solvency/provisions/summary.html)
- [SSA 2026 COLA fact sheet and national average benefits](https://www.ssa.gov/cola/factsheets/2026.html)
- [Official House Representative Finder](https://www.house.gov/representatives/find-your-representative)
- [Official Senate contacts](https://www.senate.gov/senators/senators-contact.htm)
- [Congressional Research Service: Social Security Trust Funds and Financing (Nov 2, 2026)](https://www.everycrsreport.com/reports/R49500.html)

Update core projections and policy scores after each annual Trustees Report. Do not treat the 2026 figures as current in 2027 or beyond without re-checking.

## Testing

Static validation, pure logic tests, and DOM integration simulation (run without a real browser):

```bash
python3 tests/validate.py
node tests/unit-tests.cjs
node tests/dom-integration.cjs
```

`tests/smoke.py` is an optional Playwright HTTP-navigation browser end-to-end test. It starts a temporary local HTTP server itself, saves desktop/mobile screenshots to `tests/test-output/`, and requires a Chromium environment that permits localhost navigation. The authoring environment blocks navigation to local/localhost URLs. An additional `tests/smoke-inline.py` uses Playwright `set_content` to render the standalone file in headless Chromium without network navigation and passed desktop/mobile interaction checks, including benefit/policy calculations, ZIP state routing, letter creation and download, and layout overflow. This is NOT a full external-HTTP deployment test.

## Project structure

- `index.html` — standalone deployed HTML, CSS and JavaScript in one file.
- `index.source.html` — editable modular semantic markup, official citations and UI structure.
- `styles.css` — responsive design, interactive cards, accessibility/reduced-motion support.
- `app.js` — chart, benefits calculator, policy model, senator/House links, letter draft/download.
- `tests/` — static/logic tests; optional browser smoke test.

## Editorial stance

The site does **not** endorse parties, candidates, or specific reforms. Letter templates let people state their own priorities. The illustrative benefit scenarios are not personalized SSA forecasts, and source projections are not guaranteed future outcomes.

## License

MIT (code). U.S. government facts and sources are attributed through links; SSA is not affiliated with or endorsing this project.

## Portfolio gallery and annotated walkthrough

The project has seven actual local Chromium screenshot captures (four desktop, three mobile), a 7-step manually paced browser walkthrough (optional 20 seconds per step, pausable), and a full source-linked user manual. They are published in the shared [portfolio demo gallery](https://cal2020.github.io/hello-world-app/demos/) and do not represent screenshots of an unrestricted live-URL session.

This release also contains a `source.zip` in the portfolio-hosted mirror for easy self-hosting. The canonical maintained source branch is `cal2020/webdev`, `release/social-security-explained`.
## November 9, 2026 — Congressional contact usability update

- People can select Senator, Representative or Delegate / Resident Commissioner and enter a verified officeholder name; the letter then uses that office and name. A generic salutation remains available.
- A current-Congress notice explains why November 2026 election winners do not yet appear as serving representatives on the House.gov lookup.
- ZIP-boundary guidance makes clear that a five-digit ZIP is not guaranteed to identify one district; the official lookup may request ZIP+4 or a street address on House.gov.
- Fixed `[hidden]` styling so irrelevant ZIP controls are not displayed for D.C. or U.S. territories.
- Browser-local desktop/mobile Chromium contact-flow tests passed. External HTTPS navigation and iOS Safari remain unverified. No messages are sent automatically and no officeholder names are inferred from ZIP codes.

Source: https://www.house.gov/representatives/find-your-representative
