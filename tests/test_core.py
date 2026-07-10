import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from ai_context_core.classifier import classify_file, detect_project_types
from ai_context_core.config import LEGACY_ALLOWED_EXTS
from ai_context_core.report import build_report_text
from ai_context_core.scanner import scan_project
from ai_context_core.selection import (
    automatic_select,
    build_extension_groups,
    build_folder_groups,
    interactive_select,
)


class AiContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, rel_path: str, content: bytes) -> None:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def scan(self, **kwargs):
        options = dict(
            use_git=False,
            auto_git=False,
            changed_only=False,
            excluded_dirs=set(),
            excluded_files=set(),
            excluded_exts=set(),
            targets=set(),
            max_size_kb=0,
            force_include=set(),
            smart_map=False,
        )
        options.update(kwargs)
        return scan_project(str(self.root), **options)

    def test_detects_python_project_and_extensionless_file(self):
        self.write("pyproject.toml", b"[project]\nname='x'\n")
        self.write("app.py", b"print('ok')\n")
        self.write("Dockerfile", b"FROM python:3.12\n")
        scan = self.scan()
        self.assertIn("Python", scan.project_types)
        self.assertIn("Docker", scan.project_types)
        by_name = {item.name: item for item in scan.files}
        self.assertEqual(by_name["Dockerfile"].extension, ".dockerfile")
        self.assertTrue(by_name["Dockerfile"].default_selected)

    def test_sensitive_files_are_blocked_by_default(self):
        self.write("app.py", b"print('ok')\n")
        self.write(".env", b"API_KEY=secret\n")
        scan = self.scan()
        selection = automatic_select(
            scan,
            allowed_exts=set(LEGACY_ALLOWED_EXTS),
            unsafe=True,
            allow_sensitive=False,
            force_include=set(),
            budget=0,
        )
        self.assertIn("app.py", selection.selected_paths)
        self.assertNotIn(".env", selection.selected_paths)
        self.assertIn(".env", selection.blocked_sensitive_paths)

    def test_force_include_can_add_exact_sensitive_file(self):
        self.write(".env", b"EXAMPLE_ONLY=yes\n")
        scan = self.scan(force_include={".env"})
        selection = automatic_select(
            scan,
            allowed_exts=set(LEGACY_ALLOWED_EXTS),
            unsafe=False,
            allow_sensitive=False,
            force_include={".env"},
            budget=0,
        )
        self.assertIn(".env", selection.selected_paths)

    def test_binary_is_listed_but_not_read(self):
        self.write("image.png", b"\x89PNG\r\n\x1a\n\x00binary")
        scan = self.scan()
        selection = automatic_select(
            scan,
            allowed_exts=set(LEGACY_ALLOWED_EXTS),
            unsafe=False,
            allow_sensitive=False,
            force_include=set(),
            budget=0,
        )
        self.assertIn("image.png", selection.selected_paths)
        text, content_count, binary_count, names_only_count = build_report_text(
            scan, selection, tree_only=False
        )
        self.assertIn("[BINARY DOSYA", text)
        self.assertEqual(content_count, 0)
        self.assertEqual(binary_count, 1)

    def test_budget_moves_largest_files_to_names_only(self):
        self.write("small.py", b"x=1\n")
        self.write("large.py", b"x='" + b"a" * 4000 + b"'\n")
        scan = self.scan()
        selection = automatic_select(
            scan,
            allowed_exts=set(LEGACY_ALLOWED_EXTS),
            unsafe=False,
            allow_sensitive=False,
            force_include=set(),
            budget=100,
        )
        self.assertIn("large.py", selection.names_only_paths)
        self.assertLessEqual(selection.estimated_tokens, 100)

    def test_excluded_extension_and_target(self):
        self.write("a.py", b"a=1\n")
        self.write("b.js", b"b=1;\n")
        scan = self.scan(excluded_exts={".js"}, targets={"a.py"})
        self.assertEqual([item.rel_path for item in scan.files], ["a.py"])

    def test_extension_groups_keep_binary_separate(self):
        self.write("a.py", b"a=1\n")
        self.write("x.png", b"\x89PNG")
        scan = self.scan()
        groups = build_extension_groups(scan.files)
        keys = {group.key for group in groups}
        self.assertIn(".py", keys)
        self.assertIn(".png", keys)

    def test_git_scanner_respects_gitignore_when_git_available(self):
        try:
            subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git bulunamadı")

        subprocess.run(["git", "init"], cwd=self.root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.write(".gitignore", b"ignored.py\n")
        self.write("kept.py", b"print('yes')\n")
        self.write("ignored.py", b"print('no')\n")
        scan = self.scan(use_git=True)
        paths = {item.rel_path for item in scan.files}
        self.assertIn("kept.py", paths)
        self.assertNotIn("ignored.py", paths)
        self.assertEqual(scan.scanner_name, "git")


    def test_legacy_selection_does_not_enable_smart_optional_types(self):
        self.write("app.py", b"print('ok')\n")
        self.write("style.css", b"body{}\n")
        self.write("README.md", b"docs\n")
        self.write("pyproject.toml", b"[project]\n")
        scan = self.scan()
        selection = automatic_select(
            scan,
            allowed_exts=set(LEGACY_ALLOWED_EXTS),
            unsafe=False,
            allow_sensitive=False,
            force_include=set(),
            budget=0,
        )
        self.assertIn("app.py", selection.selected_paths)
        self.assertNotIn("style.css", selection.selected_paths)
        self.assertNotIn("README.md", selection.selected_paths)
        self.assertNotIn("pyproject.toml", selection.selected_paths)

    def test_env_example_is_safe_and_recommended_for_interactive_mode(self):
        self.write(".env.example", b"API_URL=https://example.invalid\n")
        scan = self.scan()
        record = next(item for item in scan.files if item.rel_path == ".env.example")
        self.assertFalse(record.is_sensitive)
        self.assertTrue(record.default_selected)

    def test_dynamic_markdown_fence_survives_embedded_fence(self):
        self.write("sample.py", b"text = \"```inside```\"\n")
        scan = self.scan()
        selection = automatic_select(
            scan,
            allowed_exts=set(LEGACY_ALLOWED_EXTS),
            unsafe=False,
            allow_sensitive=False,
            force_include=set(),
            budget=0,
        )
        text, _, _, _ = build_report_text(scan, selection, tree_only=False)
        self.assertIn("````py", text)

    def test_interactive_default_selects_only_recommended_files_in_partial_group(self):
        self.write("package.json", b"{\"name\": \"demo\"}\n")
        self.write("large-data.json", b"[1,2,3]\n")
        scan = self.scan()
        groups = build_extension_groups(scan.files)
        json_group = next(group for group in groups if group.key == ".json")
        self.assertTrue(json_group.partially_selected)
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
            selection = interactive_select(
                scan, budget=0, allow_sensitive=False, force_include=set()
            )
        self.assertIn("package.json", selection.selected_paths)
        self.assertNotIn("large-data.json", selection.selected_paths)

    def test_changed_only_with_clean_repo_selects_nothing(self):
        try:
            subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git bulunamadı")

        subprocess.run(["git", "init"], cwd=self.root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.root, check=True)
        self.write("clean.py", b"print('clean')\n")
        subprocess.run(["git", "add", "clean.py"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        scan = self.scan(changed_only=True)
        self.assertEqual(scan.files, [])


    def test_smart_map_shows_pruned_directories_without_scanning_contents(self):
        self.write("app/main.php", b"<?php echo 1;\n")
        self.write("env/Lib/site-packages/noise.py", b"noise = True\n")
        self.write("uploads/photo.png", b"PNG")
        scan = self.scan(smart_map=True)
        paths = {item.rel_path for item in scan.files}
        self.assertIn("app/main.php", paths)
        self.assertNotIn("env/Lib/site-packages/noise.py", paths)
        dirs = {item.rel_path: item for item in scan.structure_entries if item.kind == "dir"}
        self.assertTrue(dirs["env"].is_pruned)
        self.assertTrue(dirs["uploads"].is_pruned)

    def test_folder_plan_maps_assets_and_summarizes_runtime_folders(self):
        self.write("app/main.php", b"<?php echo 1;\n")
        self.write("assets/css/site.css", b"body{}\n")
        self.write("assets/img/hero.webp", b"RIFFWEBP")
        self.write("docs/architecture.md", b"# Architecture\n")
        self.write(".agents/rules.md", b"# Rules\n")
        self.write(".env", b"SECRET=value\n")
        self.write("env/Lib/noise.py", b"noise=True\n")
        self.write("uploads/photo.png", b"PNG")
        scan = self.scan(smart_map=True)
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
            selection = interactive_select(
                scan, budget=0, allow_sensitive=False, force_include=set(), map_limit=120
            )
        self.assertIn("app/main.php", selection.selected_paths)
        self.assertIn("assets/css/site.css", selection.selected_paths)
        self.assertNotIn("assets/img/hero.webp", selection.selected_paths)
        self.assertIn("assets/img/hero.webp", selection.map_file_paths)
        self.assertIn("docs/architecture.md", selection.map_file_paths)
        self.assertNotIn("docs/architecture.md", selection.selected_paths)
        self.assertIn("env", selection.summary_dirs)
        self.assertIn("uploads", selection.summary_dirs)
        self.assertIn(".env", selection.blocked_sensitive_paths)

    def test_docs_file_can_be_picked_individually(self):
        self.write("app/main.php", b"<?php echo 1;\n")
        self.write("docs/architecture.md", b"# Architecture\n")
        self.write("docs/old-notes.txt", b"old\n")
        scan = self.scan(smart_map=True)
        groups = build_folder_groups(scan)
        docs_index = next(index for index, group in enumerate(groups, 1) if group.key == "docs")
        answers = iter([str(docs_index), "5", "1", ""])
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", side_effect=lambda *_: next(answers)):
            selection = interactive_select(
                scan, budget=0, allow_sensitive=False, force_include=set(), map_limit=120
            )
        self.assertIn("docs/architecture.md", selection.selected_paths)
        self.assertNotIn("docs/old-notes.txt", selection.selected_paths)
        self.assertIn("docs/old-notes.txt", selection.map_file_paths)

    def test_report_contains_full_map_but_only_selected_contents(self):
        self.write("app/main.php", b"<?php echo 'APP';\n")
        self.write("assets/img/hero.webp", b"RIFFWEBP")
        self.write("docs/architecture.md", b"SECRET_DOC_TEXT\n")
        self.write("env/Lib/noise.py", b"NOISE_CONTENT\n")
        scan = self.scan(smart_map=True)
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
            selection = interactive_select(
                scan, budget=0, allow_sensitive=False, force_include=set(), map_limit=120
            )
        text, content_count, _, _ = build_report_text(scan, selection, tree_only=False)
        self.assertIn("hero.webp [BINARY - yalnızca dosya adı]", text)
        self.assertIn("env/ [", text)
        self.assertIn("architecture.md [yalnızca dosya adı]", text)
        self.assertIn("<?php echo 'APP';", text)
        self.assertNotIn("SECRET_DOC_TEXT", text)
        self.assertNotIn("NOISE_CONTENT", text)
        self.assertEqual(content_count, 1)


    def test_interactive_excluded_extension_stays_in_map_but_not_content(self):
        self.write("app/main.php", b"<?php echo 'APP';\n")
        self.write("app/schema.sql", b"CREATE TABLE secret_table;\n")
        scan = self.scan(smart_map=True)
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
            selection = interactive_select(
                scan,
                budget=0,
                allow_sensitive=False,
                force_include=set(),
                map_limit=120,
                excluded_exts={".sql"},
            )
        self.assertIn("app/main.php", selection.selected_paths)
        self.assertIn("app/schema.sql", selection.map_file_paths)
        self.assertNotIn("app/schema.sql", selection.selected_paths)
        self.assertIn("HARİÇ UZANTI", selection.path_notes["app/schema.sql"])
        text, _, _, _ = build_report_text(scan, selection, tree_only=False)
        self.assertIn("schema.sql [HARİÇ UZANTI", text)
        self.assertNotIn("CREATE TABLE secret_table", text)

    def test_interactive_excluded_file_stays_in_map_but_not_content(self):
        self.write("app/main.php", b"<?php echo 'APP';\n")
        self.write("app/debug.php", b"<?php echo 'DEBUG';\n")
        scan = self.scan(smart_map=True)
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
            selection = interactive_select(
                scan,
                budget=0,
                allow_sensitive=False,
                force_include=set(),
                map_limit=120,
                excluded_files={"debug.php"},
            )
        self.assertIn("app/debug.php", selection.map_file_paths)
        self.assertNotIn("app/debug.php", selection.selected_paths)
        self.assertIn("HARİÇ DOSYA", selection.path_notes["app/debug.php"])

    def test_force_include_overrides_interactive_excluded_extension(self):
        self.write("app/main.php", b"<?php echo 'APP';\n")
        self.write("app/schema.sql", b"CREATE TABLE required_table;\n")
        scan = self.scan(smart_map=True, force_include={"app/schema.sql"})
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
            selection = interactive_select(
                scan,
                budget=0,
                allow_sensitive=False,
                force_include={"app/schema.sql"},
                map_limit=120,
                excluded_exts={".sql"},
            )
        self.assertIn("app/schema.sql", selection.selected_paths)
        self.assertEqual(selection.path_notes["app/schema.sql"], "İÇERİK")

    def test_markerless_php_project_is_detected(self):
        self.write("index.php", b"<?php\n")
        self.write("app/page.php", b"<?php\n")
        scan = self.scan(smart_map=True)
        self.assertIn("PHP", scan.project_types)


    def test_git_smart_map_keeps_ignored_env_and_git_as_summary(self):
        try:
            subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git bulunamadı")

        subprocess.run(["git", "init"], cwd=self.root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.write(".gitignore", b"env/\n.env\n")
        self.write("app/main.php", b"<?php echo 1;\n")
        self.write("env/Lib/noise.py", b"noise=True\n")
        self.write(".env", b"SECRET=x\n")
        scan = self.scan(use_git=True, smart_map=True)
        self.assertEqual(scan.scanner_name, "git")
        self.assertNotIn("env/Lib/noise.py", {item.rel_path for item in scan.files})
        dirs = {item.rel_path: item for item in scan.structure_entries if item.kind == "dir"}
        self.assertTrue(dirs[".git"].is_pruned)
        self.assertTrue(dirs["env"].is_pruned)
        root_extra = {item.rel_path for item in scan.structure_entries if item.kind == "file"}
        self.assertIn(".env", root_extra)


if __name__ == "__main__":
    unittest.main()
