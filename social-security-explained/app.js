/* Social Security, Explained. No external dependencies; no storage, analytics or network requests. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const fmt = amount => Math.round(amount).toLocaleString('en-US', {style: 'currency', currency: 'USD', maximumFractionDigits: 0});
  const clamp = (num, low, high) => Math.max(low, Math.min(high, Number.isFinite(num) ? num : low));
  const sourceRoot = 'https://www.ssa.gov/OACT/solvency/provisions/';

  // 2026 Trustees Report standalone actuarial estimates for the combined OASDI program.
  // Percentages show the 75-year actuarial shortfall addressed by each *individual* proposal.
  // They cannot be reliably summed and do NOT represent 2032 payment shortfall reductions.
  const policies = [
    {
      id:'E1.1', kind:'More revenue', name:'Increase the payroll-tax rate', short:'12.4% to 17% total, starting in 2027', percent:101,
      summary:'Increase the combined Social Security payroll-tax rate from 12.4% to 17%, beginning in 2027. The employee and employer would each generally pay 8.5% instead of 6.2%.',
      affected:'Most people with wages subject to Social Security taxes, plus employers. Self-employed workers generally pay both portions.',
      tradeoff:'Large, dependable revenue increase but lower employee take-home pay and higher employer labor costs. Closes the 75-year actuarial gap in isolation, not necessarily every annual deficit indefinitely.',
      source:sourceRoot+'payrolltax_summary.html', calc:'rate'
    },
    {
      id:'E2.1', kind:'More revenue', name:'Remove the taxable earnings cap', short:'Tax all wages, no extra benefit credit', percent:58,
      summary:'From 2027, apply the full Social Security payroll tax to covered wages above the usual taxable maximum. Under this modeled option, those newly taxed wages would not earn additional benefit credits.',
      affected:'Workers earning more than the Social Security taxable maximum (2026: $184,500), and their employers.',
      tradeoff:'Raises substantial revenue from high earnings, but changes the link between payroll contributions and later benefits. Some people would pay more without increasing their future benefit.',
      source:sourceRoot+'payrolltax_summary.html', calc:'uncap'
    },
    {
      id:'E2.17', kind:'More revenue', name:'Tax earnings over $400,000', short:'Add Social Security tax above $400k', percent:53,
      summary:'Beginning in 2027, tax earnings above $400,000 at the full 12.4% combined rate, without additional benefit credits. The gap between the regular wage ceiling and $400,000 initially remains untaxed.',
      affected:'Workers with annual covered earnings over $400,000 and their employers.',
      tradeoff:'Focuses additional taxes on very high earnings but closes only part of the long-run shortfall. The SSA model eventually taxes all earnings after the normal wage cap rises past $400,000.',
      source:sourceRoot+'payrolltax_summary.html', calc:'above400'
    },
    {
      id:'C1.6', kind:'Benefit changes', name:'Gradually move full retirement age to 69', short:'Phase up from 67; adjust delayed credits', percent:15,
      summary:'Beginning with people turning 62 in 2027, increase the full retirement age by one month every two years until it reaches 69, with the delayed-retirement-credit age also rising to 72.',
      affected:'Future retirees, especially people who cannot continue working longer or who claim at the same age as before.',
      tradeoff:'Cuts lifetime benefits for many affected cohorts. More difficult for people with physically demanding work, disabilities, or shorter life expectancies.',
      source:sourceRoot+'retireage_summary.html', calc:null
    },
    {
      id:'A2', kind:'Benefit changes', name:'Reduce annual cost-of-living increases', short:'Annual COLA reduced 0.5 percentage points', percent:24,
      summary:'Starting in December 2027, reduce the annual Social Security cost-of-living adjustment (COLA) by half a percentage point compared with the current formula.',
      affected:'People receiving benefits, with the impact accumulating over years of retirement.',
      tradeoff:'Benefits grow more slowly over time. Retirees who live the longest face a growing cumulative loss compared with current law.',
      source:sourceRoot+'cola_summary.html', calc:null
    },
    {
      id:'A3', kind:'Benefit changes', name:'Use a slower inflation index', short:'Chained CPI-W for annual increases', percent:15,
      summary:'Starting in December 2027, use a chained consumer-price index for annual cost-of-living adjustments. SSA expects it to grow around 0.3 percentage points more slowly, on average.',
      affected:'Retirees and other Social Security recipients over time.',
      tradeoff:'Some consider chained inflation more representative of substitution between products. Others argue older Americans have different spending needs, especially for health care.',
      source:sourceRoot+'cola_summary.html', calc:null
    }
  ];

  const states = [
    ['AL','Alabama'],['AK','Alaska'],['AZ','Arizona'],['AR','Arkansas'],['CA','California'],['CO','Colorado'],['CT','Connecticut'],['DE','Delaware'],['FL','Florida'],['GA','Georgia'],['HI','Hawaii'],['ID','Idaho'],['IL','Illinois'],['IN','Indiana'],['IA','Iowa'],['KS','Kansas'],['KY','Kentucky'],['LA','Louisiana'],['ME','Maine'],['MD','Maryland'],['MA','Massachusetts'],['MI','Michigan'],['MN','Minnesota'],['MS','Mississippi'],['MO','Missouri'],['MT','Montana'],['NE','Nebraska'],['NV','Nevada'],['NH','New Hampshire'],['NJ','New Jersey'],['NM','New Mexico'],['NY','New York'],['NC','North Carolina'],['ND','North Dakota'],['OH','Ohio'],['OK','Oklahoma'],['OR','Oregon'],['PA','Pennsylvania'],['RI','Rhode Island'],['SC','South Carolina'],['SD','South Dakota'],['TN','Tennessee'],['TX','Texas'],['UT','Utah'],['VT','Vermont'],['VA','Virginia'],['WA','Washington'],['WV','West Virginia'],['WI','Wisconsin'],['WY','Wyoming'],['DC','District of Columbia'],['AS','American Samoa'],['GU','Guam'],['MP','Northern Mariana Islands'],['PR','Puerto Rico'],['VI','U.S. Virgin Islands']
  ];
  const stateByCode = new Map(states);
  const withoutSenators = new Set(['DC','AS','GU','MP','PR','VI']);

  function renderFunding(mode){
    const combined = mode === 'combined', payable = combined ? 83 : 78;
    $('payableAmount').textContent = '$' + payable;
    $('coveredLegend').textContent = '$' + payable;
    $('gapLegend').textContent = '$' + (100-payable);
    $('fundHeadline').textContent = combined
      ? 'Projected to be covered in 2034 only if Congress first combines the retirement and disability funds.'
      : 'Projected to be covered by incoming revenue after retirement reserves run out.';
    $('fundQualification').textContent = combined
      ? 'Hypothetical legally combined funds; Congress would need to authorize it.'
      : 'Retirement & survivor fund only (OASI). A projection, not a voted benefit cut.';
    [...$('fundGrid').children].forEach((unit, i) => unit.classList.toggle('unfunded', i >= payable));
    document.querySelectorAll('[data-view]').forEach(button => {
      const selected = button.dataset.view === mode;
      button.classList.toggle('active', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
  }

  function renderBenefits(){
    const monthly = clamp(Number($('monthlyBenefit').value), 0, 100000);
    const scenario = Number(document.querySelector('input[name="benefitScenario"]:checked').value);
    const remaining = monthly * (100-scenario) / 100;
    const shortfall = monthly - remaining;
    $('monthlyBefore').textContent = fmt(monthly);
    $('monthlyAfter').innerHTML = ''; // Insert text and a known safe static suffix separately.
    $('monthlyAfter').append(document.createTextNode(fmt(remaining) + ' '));
    const suffix = document.createElement('span');suffix.textContent='/ month';$('monthlyAfter').append(suffix);
    $('monthlyBarAfter').textContent = fmt(remaining);
    $('barAfter').style.width = (100-scenario)+'%';
    $('monthlyLoss').textContent = shortfall ? '−'+fmt(shortfall) : '$0';
    $('annualLoss').textContent = shortfall ? '−'+fmt(shortfall*12) : '$0';
    $('snapshotPill').textContent = scenario === 22 ? '2032 scenario' : (scenario === 17 ? '2034 scenario' : 'Full payment');
  }

  function renderPolicyList(){
    policies.forEach(p => {
      const button = document.createElement('button');button.type='button';button.className='policy-card';
      button.dataset.policy = p.id;button.setAttribute('aria-pressed', 'false');
      const category = document.createElement('span');category.className='card-type';category.textContent=p.kind+' · SSA '+p.id;
      const name = document.createElement('span');name.className='card-name';name.textContent=p.name;
      const score = document.createElement('strong');score.className='card-score';score.textContent=p.percent+'%';
      button.append(category,name,score);
      button.title = p.short;
      button.addEventListener('click',()=>renderPolicy(p.id));
      $('policyList').append(button);
    });
    renderPolicy('E2.17');
  }
  let activePolicy = null;
  function renderPolicy(id){
    activePolicy = policies.find(p=>p.id===id)||policies[0];
    const p=activePolicy;
    document.querySelectorAll('[data-policy]').forEach(b=>{const active=b.dataset.policy===p.id;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
    $('policyTag').textContent = p.kind.toUpperCase() + ' · OPTION ' + p.id;
    $('policyName').textContent = p.name;
    $('policySummary').textContent = p.summary;
    $('policyPercent').textContent = p.percent + '%';
    $('policyMeterFill').style.width=Math.min(100,p.percent)+'%';
    $('policyAffected').textContent = p.affected;
    $('policyTradeoff').textContent = p.tradeoff;
    $('policySource').href=p.source;
    $('taxMini').hidden=!p.calc;
    if(p.calc)renderTaxImpact();
  }

  function calculateExtraTax(id, annualWages){
    // Employee share only. A simplified 2026-wage-base comparison against current law.
    const wages = clamp(annualWages,0,10000000);
    if(id==='E1.1')return Math.round(Math.min(wages,184500) * 0.023 * 100) / 100;
    if(id==='E2.1')return Math.round(Math.max(0,wages-184500) * 0.062 * 100) / 100;
    if(id==='E2.17')return Math.round(Math.max(0,wages-400000) * 0.062 * 100) / 100;
    return 0;
  }
  function renderTaxImpact(){if(activePolicy)$('extraTax').textContent=fmt(calculateExtraTax(activePolicy.id,Number($('annualEarnings').value)));}

  function renderStateLinks(){
    const code=$('stateSelect').value;
    const state=stateByCode.get(code);
    const noSenators=withoutSenators.has(code);
    const senate=$('senateLink');
    senate.hidden=noSenators;
    $('senateHeading').textContent=noSenators?'No U.S. Senators':'Your 2 U.S. Senators';
    $('senateDescription').textContent=noSenators
      ?'Washington, D.C. and U.S. territories do not have senators. You can contact your House delegate or resident commissioner.'
      :'Both senators from your state vote on Social Security legislation.';
    senate.href=(state&&!noSenators)?`https://www.senate.gov/states/${code}/intro.htm`:'https://www.senate.gov/senators/senators-contact.htm';
    senate.firstChild.textContent=state?`See current ${state} senators on Senate.gov `:'Choose a state above to find senators ';
    const house=$('houseLink');
    $('houseHeading').textContent=noSenators?'Your House Delegate / Resident Commissioner':'Your U.S. House Representative';
    $('houseDescription').textContent=noSenators
      ?'See the official House directory for the delegate or resident commissioner representing your district or territory.'
      :'Your congressional district determines your House member. Some ZIP codes span more than one district.';
    house.href=noSenators?'https://www.house.gov/representatives':'https://www.house.gov/representatives/find-your-representative';
    const zip=$('zipInput').value.trim();
    const valid=/^[0-9]{5}$/.test(zip);
    $('copyZip').hidden=!(valid&&!noSenators);
    house.firstChild.textContent=noSenators?'See your delegate / commissioner in the House directory ':(valid?'Find your House member using ZIP '+zip+' on House.gov ':'Find your House member on House.gov ');
  }
  function createDraft(){
    const state=stateByCode.get($('stateSelect').value)||'[your state]';
    const city=$('cityInput').value.trim();
    const zip=$('zipInput').value.trim();
    const location=[city,state,/^[0-9]{5}$/.test(zip)?zip:''].filter(Boolean).join(', ').replace(/, (\d{5})$/,' $1');
    const name=$('senderName').value.trim();
    const personal=$('personalStory').value.trim();
    const view=$('letterApproach').value;
    const office=$('recipientOffice').value;
    const officeName=$('recipientName').value.replace(/[\r\n\t]+/g,' ').replace(/\s+/g,' ').trim().slice(0,120);
    const titles={senator:'Senator',representative:'Representative',delegate:'Delegate / Resident Commissioner'};
    const salutation=(officeName&&titles[office])?`Dear ${titles[office]} ${officeName},`:'Dear Member of Congress,';
    const openings={
      balanced:'I am asking you to work across party lines on an actionable Social Security financing agreement before the projected 2032 retirement trust fund depletion date. Please explain which mix of revenue and benefit changes you support, and what that mix means for current and future beneficiaries.',
      protect:'Please prioritize protecting retirement and survivor benefits, especially for people who depend on them for essentials. I would like to know how you would fund those commitments sustainably without sudden reductions for current beneficiaries.',
      future:'I want a Social Security solution that is sustainable and fair to younger and future workers. Please explain how your proposal shares the cost across generations and protects people with low lifetime earnings.',
      accountable:'Please publish and support a credible, actuarially scored plan to keep Social Security adequately funded. Voters deserve specifics about costs, taxes, benefit changes, transition periods and long-run financial effects—not just promises.'
    };
    $('letterSubject').value="Please act on Social Security's financing before 2032";
    const lines=[
      salutation,'',
      `I am a constituent${location?' in '+location:''}. ${openings[view]||openings.balanced}`,'',
      'According to the Social Security Administration\'s 2026 Trustees Report, the retirement and survivor trust fund is projected to exhaust its reserves in late 2032. Continuing income would then be sufficient to cover only about 78% of scheduled benefits. This is a financing projection, not an enacted across-the-board benefit cut.',''
    ];
    if(personal)lines.push(personal,'');
    lines.push(
      'Please tell me: (1) what specific reforms you support, (2) how you will protect vulnerable beneficiaries and account for future workers, and (3) what you will do to help Congress act before the projected deadline.','',
      'Thank you for representing our community. I look forward to your response.','',
      'Sincerely,',name||'[Your name]'
    );
    $('letterBody').value=lines.join('\n');
    $('letterStatus').textContent='Your draft is ready. Edit it before sending.';
  }
  async function copyText(text){
    if(navigator.clipboard && window.isSecureContext){
      try{await navigator.clipboard.writeText(text);return true;}catch(e){/* fall through */}
    }
    const box=document.createElement('textarea');box.value=text;box.setAttribute('readonly','');box.style.position='fixed';box.style.top='-9999px';
    document.body.append(box);box.select();let okay=false;
    try{okay=document.execCommand('copy');}catch(e){okay=false;}
    box.remove();return okay;
  }
  function downloadText(filename,text){
    const blob=new Blob([text],{type:'text/plain;charset=utf-8'});
    const link=document.createElement('a');const url=URL.createObjectURL(blob);
    link.href=url;link.download=filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  function init(){
    // Visual: one unit per dollar out of 100.
    for(let i=0;i<100;i++){const tile=document.createElement('span');$('fundGrid').append(tile);}
    renderFunding('oasi');
    document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>renderFunding(b.dataset.view)));
    $('explainChart').addEventListener('click',()=>{const dialog=$('chartDialog');if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','');});
    $('closeDialog').addEventListener('click',()=>$('chartDialog').close());
    $('chartDialog').addEventListener('click',e=>{if(e.target===$('chartDialog'))$('chartDialog').close();});

    $('monthlyBenefit').addEventListener('input',()=>{
      const val=clamp(Number($('monthlyBenefit').value),0,100000);
      $('benefitRange').value=String(clamp(val,500,6000));renderBenefits();
    });
    $('benefitRange').addEventListener('input',()=>{$('monthlyBenefit').value=$('benefitRange').value;renderBenefits();});
    document.querySelectorAll('[data-benefit]').forEach(b=>b.addEventListener('click',()=>{$('monthlyBenefit').value=b.dataset.benefit;$('benefitRange').value=b.dataset.benefit;renderBenefits();}));
    document.querySelectorAll('input[name="benefitScenario"]').forEach(b=>b.addEventListener('change',renderBenefits));
    renderBenefits();renderPolicyList();$('annualEarnings').addEventListener('input',renderTaxImpact);
    states.forEach(([code,name])=>{const option=document.createElement('option');option.value=code;option.textContent=name;$('stateSelect').append(option);});
    $('stateSelect').addEventListener('change',renderStateLinks);
    $('zipInput').addEventListener('input',()=>{$('zipInput').value=$('zipInput').value.replace(/[^0-9]/g,'').slice(0,5);renderStateLinks();});
    $('copyZip').addEventListener('click',async()=>{const ok=await copyText($('zipInput').value);$('letterStatus').textContent=ok?'ZIP code copied. Paste it on House.gov.':'Could not copy ZIP. Enter it on House.gov.';});
    $('draftLetter').addEventListener('click',createDraft);
    ['recipientOffice','recipientName'].forEach(id=>$(id).addEventListener('change',()=>{$('letterStatus').textContent='Click Create / refresh my letter to use the selected office.';}));
    $('copyLetter').addEventListener('click',async()=>{const ok=await copyText($('letterBody').value);$('letterStatus').textContent=ok?'Message copied. Paste it into your representative’s contact form.':'Copy not available in this browser. Select the letter and copy it manually.';});
    $('copySubject').addEventListener('click',async()=>{const ok=await copyText($('letterSubject').value);$('letterStatus').textContent=ok?'Subject copied.':'Copy not available; select the subject and copy it manually.';});
    $('shareFacts').addEventListener('click',async()=>{
      const summary='Social Security is not disappearing. SSA’s 2026 Trustees Report projects that retirement & survivor reserves will be exhausted in late 2032. Continuing income would cover about 78% of scheduled benefits; Congress can change that outcome. The disability trust fund is separately projected solvent through 2100. These are funding projections, not a law mandating a uniform 22% cut. Source: https://www.ssa.gov/news/en/press/releases/2026-06-09.html';
      const ok=await copyText(summary);$('shareStatus').textContent=ok?'Fact-checked summary copied.':'Could not copy; use the SSA source link below.';
    });
    $('downloadLetter').addEventListener('click',()=>{downloadText('social-security-letter.txt','Subject: '+$('letterSubject').value+'\n\n'+$('letterBody').value);$('letterStatus').textContent='Saved as social-security-letter.txt.';});
    createDraft();renderStateLinks();
  }
  // Useful test hooks, with no sensitive/user information exposed.
  window.SSExplained={calculateExtraTax,policies:policies.map(p=>({id:p.id,percent:p.percent})),fmt};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();