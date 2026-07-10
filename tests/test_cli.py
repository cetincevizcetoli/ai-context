import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from ai_context_core.cli import main


class CliTests(unittest.TestCase):
    def test_legacy_command_creates_report(self):
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as output:
            Path(project, "app.py").write_text("print('ok')\n", encoding="utf-8")
            code = main([project, "-tk", "--output", output, "--no-open"])
            self.assertEqual(code, 0)
            reports = list(Path(output).glob("AI_CONTEXT_*.md"))
            self.assertEqual(len(reports), 1)
            self.assertIn("app.py", reports[0].read_text(encoding="utf-8-sig"))


    def test_interactive_exclude_extension_keeps_name_in_map(self):
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as output:
            Path(project, "app").mkdir()
            Path(project, "app", "main.php").write_text("<?php echo 'APP';\n", encoding="utf-8")
            Path(project, "app", "schema.sql").write_text("CREATE TABLE hidden_content;\n", encoding="utf-8")
            with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
                code = main([
                    project, "-it", "-xe", "sql", "--budget", "0",
                    "--output", output, "--no-open",
                ])
            self.assertEqual(code, 0)
            report = next(Path(output).glob("AI_CONTEXT_*.md")).read_text(encoding="utf-8-sig")
            self.assertIn("schema.sql [HARİÇ UZANTI", report)
            self.assertNotIn("CREATE TABLE hidden_content", report)
            self.assertIn("<?php echo 'APP';", report)

    def test_noninteractive_exclude_extension_keeps_legacy_behavior(self):
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as output:
            Path(project, "main.php").write_text("<?php echo 'APP';\n", encoding="utf-8")
            Path(project, "schema.sql").write_text("CREATE TABLE omitted;\n", encoding="utf-8")
            code = main([project, "-xe", "sql", "--output", output, "--no-open"])
            self.assertEqual(code, 0)
            report = next(Path(output).glob("AI_CONTEXT_*.md")).read_text(encoding="utf-8-sig")
            self.assertNotIn("schema.sql", report)
            self.assertNotIn("CREATE TABLE omitted", report)

    def test_unknown_argument_is_not_silently_ignored(self):
        with self.assertRaises(SystemExit) as context:
            main(["--definitely-unknown"])
        self.assertNotEqual(context.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
