from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
html=Path('/mnt/data/Social-Security-Explained.html').read_text()
css=(ROOT/'representative-finder.css').read_text()
js=(ROOT/'representative-finder.js').read_text()
out=ROOT/'screenshots'
out.mkdir(exist_ok=True)
with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for mode,w,h in [('desktop',1440,900),('mobile',390,844)]:
    page=b.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
    page.set_content(html)
    page.add_style_tag(content=css)
    page.add_script_tag(content=js)
    page.select_option('#stateSelect','CA')
    page.fill('#zipInput','94510')
    page.locator('#verified-finder').screenshot(path=str(out/(mode+'.png')))
    with Image.open(out/(mode+'.png')) as im:
      im.save(out/(mode+'.webp'),format='WEBP',quality=86,method=5)
    print(mode,'png', (out/(mode+'.png')).stat().st_size,'webp',(out/(mode+'.webp')).stat().st_size)
    page.close()
  b.close()