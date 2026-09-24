import re, tempfile, unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

class Phase323FunctionContract(unittest.TestCase):
    def test_all_inline_button_handlers_resolve(self):
        js=(Path(__file__).resolve().parents[1]/'app.js').read_text(encoding='utf8')
        defined=set(re.findall(r'(?m)^(?:async )?function\s+([A-Za-z_$][\w$]*)\s*\(',js))
        onclicks=re.findall(r'onclick=["\']([^"\']+)["\']',js)
        # Extract application function calls from inline handlers; ignore DOM methods/arrow expressions.
        called=set()
        for h in onclicks:
            for name in re.findall(r'(?<![.\w])([A-Za-z_$][\w$]*)\s*\(',h):
                if name not in {'alert','setTimeout','setInterval','encodeURIComponent','Number','String','confirm'}:
                    called.add(name)
        missing=sorted(x for x in called if x not in defined and x not in {'close'})
        self.assertEqual(missing,[])

    def test_root_and_static_assets_are_identical(self):
        base=Path(__file__).resolve().parents[1]
        self.assertEqual((base/'app.js').read_bytes(),(base/'static/app.js').read_bytes())
        self.assertEqual((base/'app.css').read_bytes(),(base/'static/app.css').read_bytes())
        self.assertEqual((base/'index.html').read_bytes(),(base/'static/index.html').read_bytes())
        self.assertNotIn("document.querySelector('.modal').remove()",(base/'app.js').read_text())
        self.assertEqual((base/'app.js').read_text().count('function modal('),1)

    def test_task_status_contract_is_unified(self):
        self.assertEqual(app.TASK_STATUS_VALUES,('Starting','Ongoing','Held Up','Finished'))
        self.assertEqual(app.task_progress('Starting',55),0)
        self.assertEqual(app.task_progress('Ongoing',55),55)
        self.assertEqual(app.task_progress('Held Up',55),55)
        self.assertEqual(app.task_progress('Finished',55),100)
        self.assertEqual(app.task_progress('Not Started',55),0)
        self.assertEqual(app.task_progress('Started',55),55)

if __name__=='__main__': unittest.main()
