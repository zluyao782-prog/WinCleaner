import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core import cleaner, process_mgr


class CleanerSafetyTests(unittest.TestCase):
    def test_build_allowed_roots_from_patterns(self):
        roots = cleaner._build_allowed_roots(
            [
                r"C:\Users\Test\AppData\Local\Temp\*",
                r"C:\Windows\Logs\*\*.log",
            ]
        )
        self.assertIn(cleaner._normalize_path(r"C:\Users\Test\AppData\Local\Temp"), roots)
        self.assertIn(cleaner._normalize_path(r"C:\Windows\Logs"), roots)

    def test_only_allow_paths_under_configured_root(self):
        allowed_roots = {
            cleaner._normalize_path(r"C:\Users\Test\AppData\Local\Temp"),
        }
        self.assertTrue(
            cleaner._is_path_allowed(
                r"C:\Users\Test\AppData\Local\Temp\cache\a.tmp",
                allowed_roots,
            )
        )
        self.assertFalse(
            cleaner._is_path_allowed(
                r"C:\Users\Test\Documents\important.docx",
                allowed_roots,
            )
        )

    def test_load_junk_profiles_expands_env_vars(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "junk_profiles.json"
            config_path.write_text(
                json.dumps({"测试": [r"%USERPROFILE%\Temp\*"]}),
                encoding="utf-8",
            )
            with patch.object(cleaner, "CONFIG_PATH", config_path):
                with patch.dict("os.environ", {"USERPROFILE": r"C:\Users\Tester"}):
                    profiles = cleaner.load_junk_profiles()
        self.assertEqual(profiles["测试"], [r"C:\Users\Tester\Temp\*"])


class ProcessProtectionTests(unittest.TestCase):
    def test_load_protected_processes_from_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "protected_procs.json"
            config_path.write_text(
                json.dumps({"protected_processes": ["System", "Custom.exe"]}),
                encoding="utf-8",
            )
            with patch.object(process_mgr, "CONFIG_PATH", config_path):
                protected = process_mgr.load_protected_processes()
        self.assertEqual(protected, {"system", "custom.exe"})

    def test_load_level_uses_stricter_thresholds(self):
        self.assertEqual(process_mgr.get_load_level(85, 100), "high")
        self.assertEqual(process_mgr.get_load_level(55, 100), "warning")
        self.assertEqual(process_mgr.get_load_level(10, 100), "normal")


if __name__ == "__main__":
    unittest.main()
