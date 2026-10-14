from pathlib import Path
from playwright.sync_api import sync_playwright
import json
p=Path(__file__).resolve().parent
with sync_playwright() as w:
 b=w.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-background-networking'])
 page=b.new_page(viewport={'width':720,'height':720},device_scale_factor=1)
 page.route('http://**/*',lambda route:route.abort());page.route('https://**/*',lambda route:route.abort())
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto((p/'marquee-gallery-browser-probe.html').as_uri())
 page.wait_for_selector('#evidence',timeout=30000)
 report=json.loads(page.locator('#evidence').inner_text());report['browser_version']=b.version;report['page_errors']=errors
 report['limits']=['This executes extracted standalone Canvas code in desktop Chrome, not Android WebView or the installed app.','ReactNativeWebView bridge is a local mock.','Actual phone font metrics and output may differ.','No FFmpeg/device conversion/upload occurs.']
 (p/'marquee-gallery-browser-replay.json').write_text(json.dumps(report,indent=2)+'\n')
 print({k:v for k,v in report.items() if k!='jpeg_lengths'})
 b.close()
