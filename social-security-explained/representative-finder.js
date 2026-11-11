/* Social Security, Explained — verified-constituent finder v1.2.
   No analytics, cookies, localStorage or URL address parameters. Names come from
   official US House Clerk and US Senate feeds; House geography from US Census.
   User consents before full street address is sent to Census via lookup service.
*/
(() => {
  'use strict';
  const API = 'https://social-security-civic-lookup.onrender.com/api/lookup';
  const HOUSE = 'https://www.house.gov/representatives/find-your-representative';
  const SENATE = 'https://www.senate.gov/senators/contact/';
  const byId = id => document.getElementById(id);
  let requestController = null;
  let requestNumber = 0;

  const markup = `
  <section class="verified-finder" aria-labelledby="verified-finder-title" id="verified-finder">
    <div class="verified-finder-heading"><span class="verified-mark" aria-hidden="true">✦</span><div><div class="verified-kicker">OFFICIAL-SOURCE LOOKUP · 119TH CONGRESS</div><h4 id="verified-finder-title">Find your lawmakers</h4><p>See who represents you <strong>right now</strong>. A state alone finds your senators. Add an address for your exact House district.</p></div></div>
    <div class="verified-form">
      <div class="verified-field"><label for="finderStreet">Street address <span>(optional)</span></label><input id="finderStreet" type="text" maxlength="110" placeholder="123 Example St" autocomplete="street-address" aria-describedby="finderPrivacy"></div>
      <div class="verified-field"><label for="finderCity">City <span>(for street lookup)</span></label><input id="finderCity" type="text" maxlength="75" autocomplete="address-level2" placeholder="e.g. Vallejo"></div>
    </div>
    <div class="verified-privacy" id="finderPrivacy"><span aria-hidden="true">🔐</span><div><strong>Your address isn't saved by this website.</strong> If you enter a street address and click Find, it is sent over HTTPS to our Render lookup service, then to the <a href="https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html" target="_blank" rel="noopener noreferrer">U.S. Census Geocoder</a>. Those services may keep infrastructure logs. No account, advertising, tracking, or automatic letter sending.</div></div>
    <label class="finder-consent" id="finderConsentWrap" hidden><input type="checkbox" id="finderConsent"><span>I agree to send this address to the lookup service and Census for a one-time district match.</span></label>
    <div class="finder-controls"><button type="button" id="finderLookup" class="btn btn-dark finder-button"><span aria-hidden="true">⌕</span> Find my current lawmakers</button><span id="finderStatus" role="status" aria-live="polite">Choose a state above to begin.</span></div>
    <div id="finderResults" class="finder-results" aria-label="Current congressional officials" aria-live="polite" hidden></div>
    <div class="finder-sources"><strong>Where the names come from</strong><a target="_blank" rel="noopener noreferrer" href="https://clerk.house.gov/xml/lists/MemberData.xml">House Clerk ↗</a><a target="_blank" rel="noopener noreferrer" href="https://www.senate.gov/general/contact_information/senators_cfm.xml">U.S. Senate ↗</a><a target="_blank" rel="noopener noreferrer" href="https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html">Census district lookup ↗</a></div>
  </section>`;

  function officialLink(href, chamber) {
    try {
      const u = new URL(href);
      const host = u.hostname.toLowerCase();
      if (u.protocol !== 'https:' || u.username || u.password || u.port) return null;
      if (chamber === 'house' && (host === 'www.house.gov' || host.endsWith('.house.gov'))) return u.href;
      if (chamber === 'senate' && (host === 'www.senate.gov' || host.endsWith('.senate.gov'))) return u.href;
    } catch (_) { /* unsafe or malformed URL */ }
    return null;
  }

  function makeLink(label, url) {
    const a = document.createElement('a');
    a.textContent = label;
    a.href = url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.className = 'finder-official-link';
    return a;
  }

  function makeCard(person) {
    const { name, kind, district, official_url, official_url_kind, phone } = person;
    const chamber = kind === 'senator' ? 'senate' : 'house';
    const card = document.createElement('article');
    card.className = 'verified-official';
    const top = document.createElement('div');
    top.className = 'verified-official-top';
    const text = document.createElement('div');
    const role = document.createElement('div');
    role.className = 'verified-role';
    role.textContent = kind === 'senator' ? 'U.S. Senator' : kind === 'delegate' ? (person.state === 'PR' ? 'Resident Commissioner' : 'House Delegate') : 'U.S. Representative';
    const heading = document.createElement('h5');
    heading.textContent = name;
    text.append(role, heading);
    if (Number.isInteger(district)) {
      const sub = document.createElement('p');
      sub.className = 'verified-district';
      sub.textContent = district ? `${person.state} · District ${district}` : `${person.state} · At-large`;
      text.append(sub);
    }
    const mark = document.createElement('span');
    mark.className = 'verified-source-mark';
    mark.textContent = 'OFFICIAL DATA';
    top.append(text, mark);
    card.append(top);

    const actions = document.createElement('div');
    actions.className = 'verified-official-actions';
    const source = officialLink(official_url, chamber) || (chamber === 'senate' ? SENATE : HOUSE);
    actions.append(makeLink(official_url_kind === 'office' && source !== HOUSE && source !== SENATE ? 'Official member website ↗' : 'Verify in official directory ↗', source));
    const use = document.createElement('button');
    use.type = 'button';
    use.className = 'finder-use';
    use.textContent = 'Use for my letter →';
    use.addEventListener('click', () => {
      const office = byId('recipientOffice');
      const officeName = byId('recipientName');
      if (!office || !officeName) return;
      office.value = kind === 'senator' ? 'senator' : kind === 'delegate' ? 'delegate' : 'representative';
      officeName.value = name;
      const draft = byId('draftLetter');
      if (draft) draft.click();
      const status = byId('finderStatus');
      if (status) status.textContent = `${name} selected. Your letter is ready to review below.`;
      const letter = document.querySelector('.action-letter');
      if (letter) letter.scrollIntoView({behavior:'smooth', block:'start'});
    });
    actions.append(use);
    card.append(actions);
    return card;
  }

  function explainHouse(status, data, streetEntered) {
    if (status === 'address_needed') return 'Your House district can cross ZIP boundaries. Add a full street address to identify the right current member, or use the official House.gov directory.';
    if (status === 'vacant_or_unverified') return `The Census returned ${data.state} District ${data.district ?? 'unknown'}, but there is no current member confirmed in the House Clerk data. This seat may be vacant or the feeds may not match. Verify at House.gov.`;
    if (status === 'census_unavailable') return `${data.district_error || 'The Census did not verify a district.'} Please use House.gov instead.`;
    return streetEntered ? 'We could not confirm this House seat. Verify at House.gov.' : 'Please use the official House directory.';
  }

  function renderResults(data, streetEntered) {
    const root = byId('finderResults');
    root.replaceChildren();
    root.hidden = false;
    const intro = document.createElement('div');
    intro.className = 'verified-results-intro';
    const title = document.createElement('h5');
    title.textContent = `Current lawmakers for ${data.state}`;
    const meta = document.createElement('p');
    const updated = data.updated_at ? new Date(data.updated_at) : null;
    const validDate = updated && !Number.isNaN(updated.getTime());
    meta.textContent = `${data.congress || 'Current'}th Congress${validDate ? ` · official roster checked ${updated.toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric'})}` : ''}`;
    intro.append(title, meta);
    root.append(intro);

    const people = [];
    // A one-word first name is not a verified officeholder identity.
    // Fail closed if an upstream roster changed its XML field layout.
    const fullName = person => person && typeof person.name === 'string' && person.name.trim().split(/\s+/).length >= 2;
    if (fullName(data.house)) people.push(data.house);
    if (Array.isArray(data.senators)) people.push(...data.senators.filter(fullName));
    if (people.length) {
      const grid = document.createElement('div');
      grid.className = 'verified-card-grid';
      people.forEach(p => grid.append(makeCard(p)));
      root.append(grid);
    }
    if (!data.house || !people.includes(data.house)) {
      const fallback = document.createElement('div');
      fallback.className = 'finder-fallback';
      const note = document.createElement('p');
      note.textContent = data.house && !people.includes(data.house) ? 'The House roster did not return a complete official name. Verify the officeholder through House.gov before sending.' : explainHouse(data.house_status, data, streetEntered);
      fallback.append(note, makeLink('Check House.gov ↗', HOUSE));
      root.append(fallback);
    }
    if (!people.length && data.state !== 'DC' && !['PR','AS','GU','MP','VI'].includes(data.state)) {
      const alert = document.createElement('p');
      alert.textContent = 'No current officials were confirmed. The official directories below are the safest next step.';
      root.append(alert);
    }
    if (data.warning) {
      const warning = document.createElement('p');
      warning.className = 'finder-warning';
      warning.textContent = data.warning;
      root.append(warning);
    }
    const note = document.createElement('p');
    note.className = 'verified-final-note';
    note.textContent = 'Only the currently serving Congress is shown. Election winners who have not taken office are excluded. Always verify the official website before sending.';
    root.append(note);
  }

  function displayError(message) {
    const status = byId('finderStatus');
    status.textContent = message;
    status.className = 'finder-error';
    const root = byId('finderResults');
    root.hidden = false;
    root.replaceChildren();
    const p = document.createElement('p');
    p.className = 'finder-fallback';
    p.textContent = 'You can still reach Congress using the official directories.';
    root.append(p,makeLink('House.gov ↗', HOUSE),makeLink('Senate.gov ↗', SENATE));
  }

  async function lookup() {
    const state = byId('stateSelect')?.value || '';
    const zip = byId('zipInput')?.value.trim() || '';
    const street = byId('finderStreet').value.trim();
    const city = byId('finderCity').value.trim();
    const status = byId('finderStatus');
    if (!state) { status.textContent = 'Choose your state or territory above first.'; byId('stateSelect')?.focus(); return; }
    if (zip && !/^\d{5}$/.test(zip)) { status.textContent = 'Use a valid five-digit ZIP or leave it empty.'; byId('zipInput')?.focus(); return; }
    if (street && !byId('finderConsent').checked) { status.textContent = 'Please agree to the one-time Census address lookup, or leave the street blank to find your senators.'; byId('finderConsent').focus(); return; }
    if (street && !city && !zip) { status.textContent = 'Add your city or ZIP for a street-address lookup.'; byId('finderCity').focus(); return; }
    if (requestController) requestController.abort();
    requestController = new AbortController();
    const requestId = ++requestNumber;
    const timeout = setTimeout(() => requestController.abort(), 38000);
    const button = byId('finderLookup');
    status.className = '';
    status.textContent = 'Checking the official congressional records…';
    button.disabled = true;
    byId('finderResults').hidden = true;
    try {
      const response = await fetch(API, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        cache: 'no-store',
        credentials: 'omit',
        referrerPolicy: 'no-referrer',
        body: JSON.stringify({state, zip, street, city}),
        signal: requestController.signal,
      });
      const data = await response.json();
      if (requestId !== requestNumber) return;
      if (!response.ok) throw Error(data.error || 'The official lookup is temporarily unavailable.');
      renderResults(data, Boolean(street));
      status.textContent = 'Official source lookup complete. Choose an office below to create your letter.';
      status.className = 'finder-success';
    } catch (e) {
      if (requestId !== requestNumber) return;
      displayError(e?.name === 'AbortError' ? 'The lookup took too long. Try again, or use the official directories.' : String(e?.message || 'The lookup could not complete.'));
    } finally {
      clearTimeout(timeout);
      if (requestId === requestNumber) button.disabled = false;
    }
  }

  function init() {
    const zipHelp = byId('zipHelp');
    if (!zipHelp || !byId('stateSelect') || byId('verified-finder')) return;
    zipHelp.insertAdjacentHTML('afterend', markup);
    zipHelp.textContent = 'Only your selected state and ZIP are used to find senators. Click Find below to send them to the lookup service; a street address is optional.';
    const recipientHelp = byId('recipientHelp');
    if (recipientHelp) recipientHelp.textContent = 'Choose a verified current officeholder using Find my lawmakers or the official chamber directory. Always review your draft before sending.';
    const street = byId('finderStreet');
    const consent = byId('finderConsentWrap');
    street.addEventListener('input', () => {
      consent.hidden = !street.value.trim();
      if (!street.value.trim()) byId('finderConsent').checked = false;
    });
    byId('finderLookup').addEventListener('click',lookup);
    byId('stateSelect').addEventListener('change', () => { if(requestController) requestController.abort();byId('finderResults').hidden = true;byId('finderStatus').textContent = 'Ready to find the current lawmakers in your selected state.'; });
  }

  // Expose only deterministic, side-effect-free helpers for the regression suite.
  window.SSRepresentativeFinder = { officialLink, explainHouse, renderResults };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();