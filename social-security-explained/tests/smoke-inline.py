"""Local capture-and-interaction test; Playwright set_content avoids restricted localhost navigation."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
from io import BytesIO

root=Path(__file__).resolve().parent.parent
html=(root/'Social-Security-Explained.html').read_text(encoding='utf-8')
out=root/'screenshots';out.mkdir(exist_ok=True)
def shot(page, name):
    png=page.screenshot(full_page=False)
    img=Image.open(BytesIO(png)).convert('RGB')
    img.save(out/(name+'.webp'),format='WEBP',quality=76,method=6)
    print('CAPTURE',name,img.size,(out/(name+'.webp')).stat().st_size)

def position(page, selector,dy=0):
    page.evaluate('''(obj)=>{ const el=document.querySelector(obj.selector);const y=el.getBoundingClientRect().top+window.scrollY+obj.dy;window.scrollTo({top:y,behavior:'instant'}) }''',{'selector':selector,'dy':dy})
    page.wait_for_timeout(180)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    desktop=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1,accept_downloads=True)
    errors=[]
    desktop.on('pageerror',lambda err:errors.append(str(err)))
    desktop.set_content(html,wait_until='load')
    desktop.wait_for_function('document.querySelectorAll("#fundGrid span").length === 100')
    assert desktop.locator('#payableAmount').inner_text()=='$78'
    assert desktop.locator('#fundGrid .unfunded').count()==22
    shot(desktop,'overview-desktop')

    desktop.get_by_role('button',name='2034 · If funds combine').click()
    assert desktop.locator('#payableAmount').inner_text()=='$83'
    assert desktop.locator('#fundGrid .unfunded').count()==17
    desktop.get_by_role('button',name='2032 · Retirement fund').click()
    assert desktop.locator('#payableAmount').inner_text()=='$78'
    assert desktop.locator('#monthlyAfter').inner_text().startswith('$2,340')
    assert desktop.locator('#annualLoss').inner_text()=='−$7,920'
    desktop.get_by_label('17% funding gap').check()
    assert desktop.locator('#annualLoss').inner_text()=='−$6,120'
    desktop.get_by_label('No reduction').check()
    assert desktop.locator('#annualLoss').inner_text()=='$0'
    desktop.locator('#monthlyBenefit').fill('5000')
    assert desktop.locator('#monthlyAfter').inner_text().startswith('$5,000')
    desktop.locator('#monthlyBenefit').fill('3000')
    desktop.get_by_label('22% funding gap').check()
    position(desktop,'#your-numbers',-95)
    shot(desktop,'benefits-desktop')

    desktop.get_by_role('button',name='Increase the payroll-tax rate').click()
    assert desktop.locator('#policyPercent').inner_text()=='101%'
    assert desktop.locator('#extraTax').inner_text()=='$2,300'
    desktop.get_by_role('button',name='Remove the taxable earnings cap').click()
    desktop.locator('#annualEarnings').fill('200000')
    assert desktop.locator('#extraTax').inner_text()=='$961'
    desktop.get_by_role('button',name='Tax earnings over $400,000').click()
    desktop.locator('#annualEarnings').fill('500000')
    assert desktop.locator('#extraTax').inner_text()=='$6,200'
    desktop.get_by_role('button',name='Increase the payroll-tax rate').click()
    desktop.locator('#annualEarnings').fill('100000')
    position(desktop,'#solutions',-80)
    shot(desktop,'solutions-desktop')

    desktop.locator('#stateSelect').select_option('CA')
    desktop.locator('#zipInput').fill('94510')
    assert 'CA/intro.htm' in desktop.locator('#senateLink').get_attribute('href')
    assert not desktop.locator('#copyZip').is_hidden()
    desktop.locator('#senderName').fill('Alex Example')
    desktop.locator('#cityInput').fill('Benicia')
    desktop.locator('#personalStory').fill('This matters to my family.')
    desktop.locator('#letterApproach').select_option('future')
    desktop.locator('#draftLetter').click()
    letter=desktop.locator('#letterBody').input_value()
    assert 'Benicia, California 94510' in letter
    assert 'This matters to my family.' in letter
    assert 'Alex Example' in letter
    assert 'younger and future workers' in letter
    with desktop.expect_download() as dl:
        desktop.locator('#downloadLetter').click()
    assert dl.value.suggested_filename=='social-security-letter.txt'
    desktop.locator('#senderName').fill('')
    desktop.locator('#cityInput').fill('')
    desktop.locator('#personalStory').fill('')
    desktop.locator('#letterApproach').select_option('balanced')
    desktop.locator('#draftLetter').click()
    position(desktop,'#action',-70)
    shot(desktop,'contact-desktop')
    desktop.locator('#explainChart').click()
    assert desktop.locator('#chartDialog').is_visible()
    desktop.locator('#closeDialog').click()
    assert not desktop.locator('#chartDialog').is_visible()
    assert not errors,errors
    print('DESKTOP PASS: 100 square chart; fund scenarios; benefit arithmetic; policy scoring; contact routing; editable letter; download; dialogs; no JS errors')

    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
    mobile.on('pageerror',lambda err:errors.append(str(err)))
    mobile.set_content(html,wait_until='load')
    mobile.wait_for_function('document.querySelectorAll("#fundGrid span").length === 100')
    size=mobile.evaluate('({scroll:document.documentElement.scrollWidth,view:innerWidth})')
    assert size['scroll']<=size['view']+1,size
    shot(mobile,'overview-mobile')
    position(mobile,'#your-numbers',-70)
    shot(mobile,'benefits-mobile')
    position(mobile,'#action',-60)
    shot(mobile,'contact-mobile')
    assert not errors,errors
    print('MOBILE PASS',size, 'no horizontal overflow or JS errors')
    browser.close()