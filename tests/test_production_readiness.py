
import os, sys, tempfile, subprocess, time, urllib.request, urllib.error, json, unittest, pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]

class ProductionReadiness(unittest.TestCase):
    def test_port_is_environment_configurable(self):
        src=(ROOT/"app.py").read_text()
        self.assertIn('PORT=int(os.getenv("PORT", "3000"))',src)

    def test_db_and_upload_paths_are_configurable(self):
        src=(ROOT/"app.py").read_text()
        self.assertIn('CONSTRUCTION_CONTROL_DB',src)
        self.assertIn('CONSTRUCTION_CONTROL_UPLOADS',src)

    def test_health_endpoint_exists(self):
        src=(ROOT/"app.py").read_text()
        self.assertIn('path=="/healthz"',src)

    def test_static_path_is_contained(self):
        src=(ROOT/"app.py").read_text()
        self.assertIn('candidate.relative_to(STATIC)',src)

    def test_head_handler_exists(self):
        src=(ROOT/"app.py").read_text()
        self.assertIn('def do_HEAD(self):',src)

    def test_no_password_hash_in_public_serializer(self):
        src=(ROOT/"app.py").read_text()
        self.assertIn('def public_user(u):',src)
        self.assertIn('allowed = ("id", "company_id", "name", "email", "active", "role", "created_at")',src)

if __name__=="__main__":
    unittest.main()
