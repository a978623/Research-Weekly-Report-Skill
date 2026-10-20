"""Portable behavioral checks; all installation/package writes use temp folders."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


metrics = load_script("report_metrics", "skills/research-weekly-report/scripts/report_metrics.py")
installer = load_script("install_skill", "scripts/install_skill.py")
validator = load_script("validate_project", "scripts/validate_project.py")
packager = load_script("package_skill", "scripts/package_skill.py")


def write(root: Path, relative: str, content: str = "public fixture\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class MetricsTests(unittest.TestCase):
    def test_unicode_codepoints_and_whitespace_are_distinct(self):
        result = metrics.report_metrics("中 A，\t文\n🧪𠀀")
        self.assertEqual(result["body_characters"], 6)
        self.assertEqual(result["body_characters_with_whitespace"], 9)
        self.assertEqual(result["whitespace_characters"], 3)
        self.assertEqual(result["han_characters"], 3)

    def test_only_visible_markdown_link_text_counts(self):
        decorated = (
            "**一、本周工作总结**\n\n"
            "阅读[完整论文名称](https://example.org/a-very-long-destination \"title\")，"
            "比较[方法][source]。\n"
            "![不应计入的中文图片说明](https://example.org/figure.png)\n"
            "<https://example.org/bare-url>\n"
            "[source]: https://example.org/reference\n\n"
            "## 二、下周工作安排\n计划比较A/B。\n"
        )
        plain = "阅读完整论文名称，比较方法。\n计划比较A/B。"
        decorated_result = metrics.report_metrics(decorated)
        plain_result = metrics.report_metrics(plain)
        self.assertEqual(decorated_result["body_characters"], plain_result["body_characters"])
        self.assertEqual(decorated_result["han_characters"], plain_result["han_characters"])

    def test_bare_urls_do_not_remove_surrounding_punctuation(self):
        self.assertEqual(metrics.visible_body("查阅 https://example.org/paper。"), "查阅 。")
        self.assertEqual(metrics.visible_body("[论文](https://example.org/paper_(v1))"), "论文")

    def test_reference_range_is_advisory_and_cli_cwd_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = write(Path(temporary), "报告.md", "计划阅读。")
            completed = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "skills/research-weekly-report/scripts/report_metrics.py"), str(report), "--json"],
                cwd=temporary, capture_output=True, text=True, encoding="utf-8", check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            import json
            result = json.loads(completed.stdout)
            self.assertFalse(result["characters_in_reference_range"])
            self.assertEqual(result["han_characters"], 4)


class InstallerTests(unittest.TestCase):
    def test_existing_target_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            write(source, "SKILL.md", "new contents")
            skills_dir = root / "installed"
            old = write(skills_dir / installer.SKILL_NAME, "SKILL.md", "old contents")
            with self.assertRaises(FileExistsError):
                installer.install_skill(source, skills_dir)
            self.assertEqual(old.read_text(encoding="utf-8"), "old contents")
            self.assertEqual(list(skills_dir.iterdir()), [old.parent])

    def test_install_copies_skill_only_to_custom_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "project" / "skills" / installer.SKILL_NAME
            write(source, "SKILL.md", "skill")
            write(source, "references/note.md", "public reference")
            write(source, "__pycache__/cached.pyc", "cache")
            write(root / "project", "README.md", "project documentation")
            target = installer.install_skill(source, root / "custom skills")
            # Windows may expose the same directory through an 8.3 short name.
            self.assertTrue(target.samefile(root / "custom skills" / installer.SKILL_NAME))
            self.assertTrue((target / "references/note.md").is_file())
            self.assertFalse((target / "README.md").exists())
            self.assertFalse((target / "__pycache__").exists())

    def test_default_respects_codex_home_and_home_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, {"CODEX_HOME": str(root / "configured")}, clear=True):
                self.assertEqual(installer.default_skills_dir(), root / "configured" / "skills")
            with patch.dict(os.environ, {}, clear=True), patch.object(installer.Path, "home", return_value=root / "home"):
                self.assertEqual(installer.default_skills_dir(), root / "home" / ".codex" / "skills")

    def test_destination_inside_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "skill"
            write(source, "SKILL.md")
            with self.assertRaises(ValueError):
                installer.install_skill(source, source / "nested")
            self.assertFalse((source / "nested").exists())


class PackageTests(unittest.TestCase):
    def test_archives_have_safe_prefixes_and_exclude_working_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            skill = root / "skills" / packager.SKILL_NAME
            write(skill, "SKILL.md", "public skill")
            write(skill, "references/public.md")
            write(skill, "__pycache__/secret.pyc")
            write(root, "README.md")
            write(root, "scripts/tool.py")
            write(root, "scripts/.env", "secret")
            write(root, "evals/case.md")
            write(root, "evals/patient.pdf", "private medical file")
            write(root, "private/notes.md", "private notes")
            write(root, "local-notes/notes.md", "private notes")
            write(root, ".git/config", "credentials")
            write(root, "unrelated-personal-note.md", "personal")
            write(root, "dist/old.zip", "old output")
            archives = packager.package_project(root, root / "dist")
            expected_prefixes = ("research-weekly-report", "research-weekly-report-skill")
            for archive_path, prefix in zip(archives, expected_prefixes):
                with zipfile.ZipFile(archive_path) as archive:
                    names = archive.namelist()
                    self.assertTrue(names)
                    for name in names:
                        parsed = PurePosixPath(name)
                        self.assertFalse(parsed.is_absolute())
                        self.assertNotIn("..", parsed.parts)
                        self.assertEqual(parsed.parts[0], prefix)
                        self.assertFalse(any(part in packager.EXCLUDED_PARTS for part in parsed.parts))
                        self.assertFalse(name.endswith((".pdf", ".pyc", ".env")))
                        self.assertNotIn("unrelated-personal-note", name)
                    self.assertTrue(any(name.endswith("/SKILL.md") for name in names))
            with zipfile.ZipFile(archives[0]) as skill_archive:
                self.assertNotIn("research-weekly-report/README.md", skill_archive.namelist())
            with zipfile.ZipFile(archives[1]) as project_archive:
                self.assertIn("research-weekly-report-skill/scripts/tool.py", project_archive.namelist())

    def test_symlink_cannot_enter_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            skill = root / "skills" / packager.SKILL_NAME
            write(skill, "SKILL.md")
            outside = write(Path(temporary), "outside.md", "private")
            try:
                (skill / "reference.md").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("This host does not allow creating symbolic links")
            with self.assertRaises(ValueError):
                packager.package_project(root, root / "dist")


class ValidatorTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        for required in validator.REQUIRED:
            write(root, required)
        write(root, "evals/case.md")
        write(root, "skills/research-weekly-report/SKILL.md", (
            "---\nname: research-weekly-report\ndescription: Write a real report.\n---\n"
            "[style](references/style-guide.md#wording)\n"
            "[template](assets/weekly-report-template.md)\n"
            "[remote](https://example.org/paper)\n"
            "[local section](#section)\n"
        ))
        write(root, "skills/research-weekly-report/assets/weekly-report-template.md", "| 论文 | 本周工作 |\n| --- | --- |\n| | |\n")
        return root / "skills/research-weekly-report/SKILL.md"

    def test_portable_fixture_and_blank_template_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            self.assertEqual(validator.validate_project(root), [])

    def test_broken_links_and_frontmatter_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = self.fixture(root)
            entry.write_text("---\nname: wrong\n---\n[broken](missing.md#section)\n", encoding="utf-8")
            errors = validator.validate_project(root)
            self.assertTrue(any("missing local link target" in error for error in errors))
            self.assertTrue(any("description" in error for error in errors))
            self.assertTrue(any("name must" in error for error in errors))

    def test_reference_links_are_checked_and_personal_paths_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = self.fixture(root)
            with entry.open("a", encoding="utf-8") as handle:
                handle.write("\n[ref]: missing-reference.md\nUser data: C:/Users/example/notes.md\n")
            errors = validator.validate_project(root)
            self.assertTrue(any("missing-reference.md" in error for error in errors))
            self.assertTrue(any("Personal absolute path" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
