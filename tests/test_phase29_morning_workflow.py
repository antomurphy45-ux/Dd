import os,sys,unittest,tempfile,sqlite3,json
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
import app

class Phase29MorningWorkflow(unittest.TestCase):
    def test_mobile_morning_ui_is_present(self):
        js=open(os.path.join(os.path.dirname(os.path.dirname(__file__)),'static','app.js'),encoding='utf-8').read()
        self.assertIn('morning-steps',js)
        self.assertIn("Everyone on site",js)
        self.assertIn("SAVE TODAY'S CONTROL",js)
        self.assertIn('updateMorningProgress',js)
    def test_css_has_mobile_morning_controls(self):
        css=open(os.path.join(os.path.dirname(os.path.dirname(__file__)),'static','app.css'),encoding='utf-8').read()
        for token in ['morning-steps','daily-progress-strip','morning-save','big-save']:
            self.assertIn(token,css)
    def test_daily_endpoint_contract_still_exists(self):
        src=open(os.path.join(os.path.dirname(os.path.dirname(__file__)),'app.py'),encoding='utf-8').read()
        self.assertIn('path=="/api/daily-site-control" and self.command=="GET"',src)
        self.assertIn('path=="/api/daily-site-control" and self.command=="POST"',src)
        self.assertIn('DAILY_SITE_CONTROL_SAVE',src)

if __name__=='__main__': unittest.main()
