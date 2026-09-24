import os, re, sqlite3, tempfile, unittest, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ProgrammeEditingContractTests(unittest.TestCase):
    def test_ui_has_easy_edit_move_delete_and_button_help(self):
        js=(ROOT/'app.js').read_text()
        self.assertIn('function moveTask(planId,taskId)',js)
        self.assertIn('function deleteTask(planId,taskId)',js)
        self.assertIn('data-help',js)
        self.assertIn('enhanceButtonHints',js)
        self.assertIn('Parent / section',js)
        self.assertIn('Save changes',js)
        self.assertIn('Move activity',js)
        self.assertIn('Delete activity',js)
        self.assertIn('Activity → Progress / Critical Path → Scheduled → Edit / Move / Delete',js)
        self.assertIn('<div>Options</div>',js)
        self.assertNotIn('<h4>Activities</h4>${rows}',js)
    def test_backend_supports_relocation_fields(self):
        py=(ROOT/'app.py').read_text()
        self.assertIn('parent=b.get("parent_id",task["parent_id"])',py)
        self.assertIn('milestone=int(bool(b.get("milestone"',py)
        self.assertIn('notes=str(b.get("notes"',py)
        self.assertIn('Invalid parent activity reference',py)
        self.assertIn('PLAN_TASK_DELETE',py)
    def test_css_has_button_explanation_and_danger_action_styles(self):
        css=(ROOT/'app.css').read_text()
        self.assertIn('button[data-help]',css)
        self.assertIn('.danger-button',css)
        self.assertIn('.programme-help-card',css)

if __name__=='__main__': unittest.main()
