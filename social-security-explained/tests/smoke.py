from pathlib import Path
from playwright.sync_api import sync_playwright
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread

root=Path(__file__).resolve().parent.parent
output=root/'test-output'
output.mkdir(exist_ok=True)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
Thread(target=server.serve_forever,daemon=True).start()
file=f'http://127.0.0.1:{server.server_port}/Social-Security-Explained.html'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium', headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1,accept_downloads=True)
    errors=[]
    page.on('pageerror',lambda err: errors.append(str(err)))
    page.goto(file)
    page.wait_for_function('document.querySelectorAll("#fundGrid span").length === 100')
    assert page.locator('#payableAmount').inner_text()=='$78'
    assert page.locator('#fundGrid .unfunded').count()==22
    page.get_by_role('button',name='2034 · If funds combine').click()
    assert page.locator('#payableAmount').inner_text()=='$83'
    assert page.locator('#fundGrid .unfunded').count()==17
    page.get_by_role('button',name='2032 · Retirement fund').click()
    assert page.locator('#monthlyAfter').inner_text().startswith('$2,340')
    assert page.locator('#annualLoss').inner_text()=='−$7,920'
    page.get_by_label('17% funding gap').check()
    assert page.locator('#monthlyAfter').inner_text().startswith('$2,490')
    assert page.locator('#annualLoss').inner_text()=='−$6,120'
    page.get_by_label('No reduction').check()
    assert page.locator('#annualLoss').inner_text()=='$0'
    page.locator('#monthlyBenefit').fill('5000')
    assert page.locator('#monthlyAfter').inner_text().startswith('$5,000')
    page.get_by_role('button',name='Increase the payroll-tax rate').click()
    assert page.locator('#policyPercent').inner_text()=='101%'
    assert page.locator('#extraTax').inner_text()=='$2,300'
    page.get_by_role('button',name='Remove the taxable earnings cap').click()
    page.locator('#annualEarnings').fill('200000')
    assert page.locator('#extraTax').inner_text()=='$961'
    page.get_by_role('button',name='Tax earnings over $400,000').click()
    page.locator('#annualEarnings').fill('500000')
    assert page.locator('#extraTax').inner_text()=='$6,200'
    page.locator('#stateSelect').select_option('CA')
    page.locator('#zipInput').fill('94510')
    assert 'CA/intro.htm' in page.locator('#senateLink').get_attribute('href')
    assert not page.locator('#copyZip').is_hidden()
    page.locator('#senderName').fill('Alex Example')
    page.locator('#cityInput').fill('Benicia')
    page.locator('#personalStory').fill('This matters to my family.')
    page.locator('#letterApproach').select_option('future')
    page.locator('#draftLetter').click()
    letter=page.locator('#letterBody').input_value()
    assert 'Benicia, California 94510' in letter
    assert 'This matters to my family.' in letter
    assert 'Alex Example' in letter
    assert 'younger and future workers' in letter
    with page.expect_download() as download:
        page.locator('#downloadLetter').click()
    assert download.value.suggested_filename=='social-security-letter.txt'
    page.locator('#explainChart').click()
    assert page.locator('#chartDialog').is_visible()
    page.locator('#closeDialog').click()
    assert not page.locator('#chartDialog').is_visible()
    page.screenshot(path=str(output/'desktop.png'),full_page=True)
    assert not errors, 'Desktop JS errors: '+repr(errors)
    print('desktop: PASS; 100-square chart, projections, benefit scenarios, policy scenarios, contact links, letter, dialog, download.')
    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,accept_downloads=True,is_mobile=True,has_touch=True)
    mobile.on('pageerror',lambda err:errors.append(str(err)))
    mobile.goto(file)
    mobile.wait_for_function('document.querySelectorAll("#fundGrid span").length === 100')
    size=mobile.evaluate('({scroll:document.documentElement.scrollWidth,view:innerWidth})')
    assert size['scroll']<=size['view']+1, 'Mobile has horizontal overflow: '+str(size)
    mobile.screenshot(path=str(output/'mobile.png'),full_page=True)
    assert not errors, 'Mobile JS errors: '+repr(errors)
    print('mobile: PASS; viewport',size,'no horizontal overflow, no JS errors')
    browser.close()
server.shutdown()