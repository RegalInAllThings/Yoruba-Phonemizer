"""Run: python tests/browser_history.py (requires Playwright + Chromium).

Install requirements-browser.txt, then `playwright install chromium`, or set
CHROMIUM_PATH to an installed Chromium. Uses real local API, never public hosting.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:8771'
KEY = 'yoruba-phonemizer.recent.v1'

class HistoryBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        python = ROOT / '.venv/bin/python'
        cls.server = subprocess.Popen([str(python) if python.exists() else sys.executable,
            '-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8771'],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.addClassCleanup(lambda: (cls.server.terminate(), cls.server.wait(timeout=10)))
        for _ in range(100):
            try:
                urllib.request.urlopen(URL + '/healthz', timeout=1)
                break
            except Exception: time.sleep(.2)
        else: raise RuntimeError('Server failed to start')
        cls.pw = sync_playwright().start()
        cls.addClassCleanup(cls.pw.stop)
        path = os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium')
        cls.browser = cls.pw.chromium.launch(executable_path=path if Path(path).exists() else None,
            headless=True, args=['--no-sandbox'])
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width':390, 'height':844},
            permissions=['clipboard-read','clipboard-write'])
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(URL)

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def entries(self):
        return self.page.locator('.history-entry').all_text_contents()

    def convert(self, text):
        self.page.locator('#text').fill(text)
        with self.page.expect_response('**/api/phonemize') as response:
            self.page.locator('#convert').click()
        self.page.wait_for_function("!document.querySelector('#convert').disabled")
        return response.value

    def test_empty_and_unsuccessful_inputs(self):
        self.assertTrue(self.page.locator('#recent').is_hidden())
        self.assertEqual(self.page.locator('[data-example]').count(), 0)
        self.page.locator('#text').fill('ẹran')
        self.assertEqual(self.entries(), [])
        self.convert('世界')
        self.assertEqual(self.entries(), [])
        self.page.route('**/api/phonemize', lambda route: route.fulfill(status=503,
            content_type='application/json', body='{"detail":"unavailable"}'))
        self.convert('ẹran')
        self.assertEqual(self.entries(), [])
        self.assertTrue(self.page.locator('#recent').is_hidden())

    def test_success_persists_and_history_is_never_sent(self):
        requests=[]
        self.page.on('request', lambda r: requests.append(json.loads(r.post_data))
            if '/api/phonemize' in r.url else None)
        self.assertEqual(self.convert('ẹran').status, 200)
        self.convert('inú')
        self.assertEqual(requests, [{'text':'ẹran'}, {'text':'inú'}])
        self.page.reload()
        self.assertEqual(self.entries(), ['inú','ẹran'])
        self.assertEqual(self.page.locator('#text').input_value(), '')

    def test_four_entries_and_duplicate_moves_to_top(self):
        for value in ['ẹran','inú','aná','ọrùn','ọ̀run']:
            self.assertEqual(self.convert(value).status, 200)
        self.assertEqual(self.entries(), ['ọ̀run','ọrùn','aná','inú'])
        self.convert('aná')
        self.assertEqual(self.entries(), ['aná','ọ̀run','ọrùn','inú'])
        # Canonically equivalent Unicode and casing do not create duplicates.
        self.convert('ANA\u0301')
        self.assertEqual(len(self.entries()), 4)
        self.assertEqual(self.entries()[0], 'ANÁ')

    def test_restore_does_not_submit_and_resets_copy(self):
        self.convert('ẹran'); self.convert('inú')
        self.page.locator('#copy').click()
        self.assertEqual(self.page.evaluate('navigator.clipboard.readText()'), '[i_M n u_H]')
        requests=[]
        self.page.on('request', lambda r: requests.append(r.url) if '/api/phonemize' in r.url else None)
        self.page.locator('.history-entry').filter(has_text='ẹran').click()
        self.page.wait_for_timeout(150)
        self.assertEqual(requests, [])
        self.assertEqual(self.page.locator('#text').input_value(), 'ẹran')
        self.assertEqual(self.page.locator('#count').inner_text(), '4 / 500')
        self.assertTrue(self.page.locator('#copy').is_disabled())
        self.assertEqual(self.page.locator('#output').inner_text(), 'Your phonemes will appear here.')

    def test_clear_survives_refresh(self):
        self.convert('ẹran')
        self.page.locator('#clear-history').click()
        self.assertTrue(self.page.locator('#recent').is_hidden())
        self.page.reload()
        self.assertEqual(self.entries(), [])

    def test_storage_blocked(self):
        self.page.add_init_script("Object.defineProperty(window, 'localStorage', {get(){throw new Error('blocked')}})")
        self.page.reload(); self.convert('ẹran')
        self.assertEqual(self.entries(), ['ẹran'])
        self.page.locator('#clear-history').click()
        self.assertTrue(self.page.locator('#recent').is_hidden())

    def test_storage_quota_exceeded(self):
        self.page.add_init_script("Storage.prototype.setItem = function(){throw new Error('quota')}")
        self.page.reload(); self.convert('ẹran')
        self.assertEqual(self.entries(), ['ẹran'])
        self.assertEqual(self.page.locator('#output').inner_text(), '[ɛ_M r ã_M]')

    def test_invalid_storage_and_plain_text_rendering(self):
        self.page.evaluate('(key) => localStorage.setItem(key, "bad json")', KEY)
        self.page.reload(); self.assertEqual(self.entries(), [])
        values=['<img src=x onerror="window.injected=true">', 42, None, '', 'a'*501]
        self.page.evaluate('([key, values]) => localStorage.setItem(key, JSON.stringify(values))', [KEY,values])
        self.page.reload()
        self.assertEqual(self.entries(), [values[0]])
        self.assertEqual(self.page.locator('#history-items img').count(),0)
        self.assertFalse(self.page.evaluate('Boolean(window.injected)'))

    def test_malformed_success_does_not_save(self):
        self.page.route('**/api/phonemize', lambda route: route.fulfill(status=200,
            content_type='application/json', body='{"phonemes":""}'))
        self.convert('ẹran'); self.assertEqual(self.entries(), [])

    def test_long_inputs_and_responsive_layout(self):
        long_text='ẹran ' * 50
        self.assertEqual(self.convert(long_text).status,200)
        self.convert('inú');self.convert('ọrùn');self.convert('aná')
        out=Path(os.environ.get('SCREENSHOT_DIR', '/tmp/yoruba-history-preview'))
        out.mkdir(parents=True,exist_ok=True)
        for width in [320,375,390,768,1440]:
            self.page.set_viewport_size({'width':width,'height':900})
            self.page.locator('#text').fill(long_text*2)
            sizes=self.page.evaluate('''() => {
                const field=document.querySelector('#text').getBoundingClientRect();
                const history=document.querySelector('#recent').getBoundingClientRect();
                const input=document.querySelector('.input-wrap').getBoundingClientRect();
                const button=document.querySelector('#convert').getBoundingClientRect();
                return {overflow:document.documentElement.scrollWidth>innerWidth,
                    overlap:field.bottom>history.top, height:field.height, correctOrder:input.bottom<=button.top};
            }''')
            self.assertFalse(sizes['overflow']); self.assertFalse(sizes['overlap'])
            self.assertTrue(sizes['correctOrder']);self.assertGreaterEqual(sizes['height'],140)
            if width in [390,1440]:
                self.page.locator('#text').fill('ẹran')
                self.page.locator('#converter').screenshot(path=str(out/f'converter-{width}.png'))
        self.page.locator('.history-entry').filter(has_text='ẹran ').click()
        self.assertEqual(self.page.locator('#text').input_value(),long_text.strip())
        self.convert('ẹran')
        self.page.locator('#text').evaluate('(element) => element.blur()')
        for width in [390,1440]:
            self.page.set_viewport_size({'width':width,'height':900})
            self.page.locator('#converter').screenshot(path=str(out/f'converter-{width}.png'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
