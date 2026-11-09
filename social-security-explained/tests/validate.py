from pathlib import Path
from bs4 import BeautifulSoup
import tinycss2, subprocess, re
P=Path(__file__).resolve().parent.parent
html=(P/'index.source.html').read_text()
css=(P/'styles.css').read_text()
js=(P/'app.js').read_text()
standalone=(P/'Social-Security-Explained.html').read_text()
soup=BeautifulSoup(html,'html.parser')
ids=[tag['id'] for tag in soup.select('[id]')]
assert len(ids)==len(set(ids)),f'duplicate IDs: {len(ids)-len(set(ids))}'
required=set(re.findall(r"\$\('([A-Za-z0-9_-]+)'\)",js))
assert not required-set(ids),f'JS missing IDs: {required-set(ids)}'
assert all(soup.select_one(f'#{i}') for i in ['fundGrid','monthlyBenefit','policyList','stateSelect','zipInput','letterBody','senateHeading','houseHeading'])
assert len(soup.select('input[name="benefitScenario"]'))==3
assert len(soup.select('a[href^="https://www.ssa.gov/"]'))>=4
assert 'https://www.house.gov/representatives/find-your-representative' in html
assert 'https://www.senate.gov/senators/senators-contact.htm' in html
assert 'No tracking' in html and 'not a benefit forecast' in html
assert not any(tag['src'].startswith('http') for tag in soup.select('script[src]'))
assert not any(tag['href'].startswith('http') for tag in soup.select('link[href]'))
assert 'fetch(' not in js and 'localStorage' not in js and 'sendBeacon' not in js
errors=[t for t in tinycss2.parse_stylesheet(css) if t.type=='error']
assert not errors, errors
assert len(standalone)>len(html)
assert '<script>' in standalone and '<style>' in standalone and 'src="app.js"' not in standalone
assert 'styles.css' not in standalone
result=subprocess.run(['node','--check',str(P/'app.js')],capture_output=True,text=True)
assert result.returncode==0,result.stderr
print('Static validation PASS: HTML ids, required elements, 3 benefit scenarios, official references, offline assets, no tracking, CSS parsed, JS syntax, single-file build.')