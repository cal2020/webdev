"""Local Chromium contact-flow regression. External deployed-site navigation is NOT exercised."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent.parent
html = (root / "Social-Security-Explained.html").read_text()
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"])
    for label, width, height in [("desktop", 1440, 900), ("mobile", 390, 844)]:
        page = browser.new_page(viewport={"width": width, "height": height})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.set_content(html)
        page.locator("#stateSelect").select_option("CA")
        page.locator("#zipInput").fill("94510")
        assert page.locator("#copyZip").is_visible()
        assert "CA/intro.htm" in page.locator("#senateLink").get_attribute("href")
        assert "January 2027" in page.locator(".current-congress-note").inner_text()
        for typ, name, opening in [
            ("senator", "Example Person", "Dear Senator Example Person,"),
            ("representative", "Example Person", "Dear Representative Example Person,"),
            ("general", "Example Person", "Dear Member of Congress,"),
        ]:
            page.locator("#recipientOffice").select_option(typ)
            page.locator("#recipientName").fill(name)
            page.locator("#draftLetter").click()
            assert page.locator("#letterBody").input_value().startswith(opening)
        page.locator("#stateSelect").select_option("PR")
        assert page.locator("#senateLink").is_hidden()
        assert page.locator("#copyZip").is_hidden()
        assert "Resident Commissioner" in page.locator("#houseHeading").inner_text()
        assert not errors, errors
        width_info = page.evaluate("({view: innerWidth, scroll: document.documentElement.scrollWidth})")
        assert width_info["scroll"] <= width_info["view"] + 1, width_info
        print(label, "PASS", width_info)
    browser.close()
