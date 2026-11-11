from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OLD=Path('/mnt/data/Social-Security-Explained.html').read_text()
CSS=(ROOT/'representative-finder.css').read_text()
JS=(ROOT/'representative-finder.js').read_text()
API='https://social-security-congress-finder.onrender.com/api/lookup'
RESP={
 'state':'CA','congress':119,'updated_at':'2026-11-11T17:00:00Z','warning':None,
 'house_status':'matched','district':4,
 'house':{'state':'CA','district':4,'kind':'representative','name':'Mike Thompson', 'official_url_kind':'office','official_url':'https://mikethompson.house.gov/'},
 'senators':[{'state':'CA','kind':'senator','name':'Adam Schiff','official_url_kind':'office','official_url':'https://www.schiff.senate.gov/contact/'},
            {'state':'CA','kind':'senator','name':'Alex Padilla','official_url_kind':'office','official_url':'https://www.padilla.senate.gov/'}]
}

with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for mode,w,h in [('desktop',1440,900),('mobile',390,844)]:
  page=browser.new_page(viewport={'width':w,'height':h})
  errors=[];reqs=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def handle(route):
   reqs.append(route.request.post_data_json)
   route.fulfill(status=200,headers={'Access-Control-Allow-Origin':'*','Content-Type':'application/json'},json=RESP)
  page.route(API,handle)
  page.set_content(OLD)
  page.evaluate('''() => {
   const div=document.createElement('div');
   div.innerHTML='<select id="recipientOffice"><option value="general">General</option><option value="senator">Senator</option><option value="representative">Representative</option><option value="delegate">Delegate</option></select><input id="recipientName">';
   document.querySelector('.action-letter').prepend(div);
  }''')
  page.add_style_tag(content=CSS)
  page.add_script_tag(content=JS)
  page.select_option('#stateSelect','CA')
  page.fill('#zipInput','94510')
  assert page.locator('#verified-finder').is_visible()
  page.click('#finderLookup')
  page.get_by_text('Mike Thompson').wait_for(timeout=5000)
  assert page.get_by_text('Mike Thompson').is_visible()
  assert page.get_by_text('Alex Padilla').is_visible()
  assert page.get_by_text('Adam Schiff').is_visible()
  assert reqs[-1]=={'state':'CA','zip':'94510','street':'','city':''}
  page.get_by_role('button',name='Use for my letter →').first.click()
  assert page.locator('#recipientOffice').input_value()=='representative'
  assert page.locator('#recipientName').input_value()=='Mike Thompson'
  assert page.locator('#finderStatus').inner_text().startswith('Mike Thompson selected')
  page.fill('#finderStreet','123 Example St')
  page.fill('#finderCity','Vallejo')
  assert page.locator('#finderConsentWrap').is_visible()
  page.click('#finderLookup')
  assert len(reqs)==1, 'Should not send address without consent'
  assert 'agree' in page.locator('#finderStatus').inner_text().lower()
  page.check('#finderConsent')
  page.click('#finderLookup')
  page.locator('#finderResults .verified-official').first.wait_for(timeout=5000)
  assert len(reqs)==2
  assert reqs[-1]['street']=='123 Example St'
  assert reqs[-1]['city']=='Vallejo'
  assert page.locator('#finderResults .verified-official').count()==3
  assert not errors, errors
  dims=page.evaluate('({viewport:window.innerWidth, body:document.documentElement.scrollWidth})')
  assert dims['body']<=dims['viewport']+1, dims
  print(mode,'PASS',dims,'3 verified office cards; consent gate; recipient insertion; privacy')
  page.close()
 browser.close()