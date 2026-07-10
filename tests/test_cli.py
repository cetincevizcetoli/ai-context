import tempfile
import unittest
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

    def test_unknown_argument_is_not_silently_ignored(self):
        with self.assertRaises(SystemExit) as context:
            main(["--definitely-unknown"])
        self.assertNotEqual(context.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
