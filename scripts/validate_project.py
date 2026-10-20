#!/usr/bin/env python3
"""Check project structure and local links; this is not a semantic evaluation."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_RELATIVE = Path("skills/research-weekly-report")
REQUIRED = (
    "README.md", "LICENSE", "scripts/install_skill.py", "scripts/validate_project.py",
    "scripts/package_skill.py", "tests/test_tools.py", ".github/workflows/validate.yml",
    "skills/research-weekly-report/SKILL.md", "skills/research-weekly-report/agents/openai.yaml",
    "skills/research-weekly-report/assets/material-intake.md",
    "skills/research-weekly-report/assets/weekly-report-template.md",
    "skills/research-weekly-report/references/style-guide.md",
    "skills/research-weekly-report/references/breast-mri.md",
    "skills/research-weekly-report/scripts/report_metrics.py",
)
LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[\"'][^\n]*[\"'])?\s*\)")
REFERENCE = re.compile(r"(?m)^\s{0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))")
PERSONAL_ABSOLUTE = re.compile(r"(?:[A-Za-z]:[\\/](?:Users|zoterodata)[\\/]|/(?:Users|home)/[^/\s]+/|file://)", re.I)
SCAFFOLD = re.compile(r"(?:\[TODO\b|\bTODO\s*:|\bFIXME\s*:|\bPLACEHOLDER\b|\[INSERT(?:\s|_)|\{\{\s*(?:TODO|INSERT|PLACEHOLDER)\b)", re.I)


def local_link_errors(path: Path, root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    errors = []
    for match in list(LINK.finditer(text)) + list(REFERENCE.finditer(text)):
        destination = next(value for value in match.groups() if value is not None)
        if destination.startswith("#"):
            continue
        parsed = urlsplit(destination)
        if parsed.scheme or parsed.netloc:
            continue
        relative = unquote(parsed.path)
        if not relative:
            continue
        target = (path.parent / relative).resolve()
        if not target.is_relative_to(root):
            errors.append(f"{path.relative_to(root)}: local link escapes project: {destination}")
        elif not target.exists():
            errors.append(f"{path.relative_to(root)}: missing local link target: {destination}")
    return errors


def validate_project(root: Path) -> list[str]:
    root = root.resolve()
    errors = [f"Missing required file: {name}" for name in REQUIRED if not (root / name).is_file()]
    for directory in ("evals",):
        path = root / directory
        if not path.is_dir() or not any(file.is_file() for file in path.rglob("*")):
            errors.append(f"Missing nonempty directory: {directory}")
    skill = root / SKILL_RELATIVE
    main = skill / "SKILL.md"
    if main.is_file():
        content = main.read_text(encoding="utf-8-sig")
        frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.S)
        if not frontmatter:
            errors.append("SKILL.md must start with YAML frontmatter")
        else:
            for key in ("name", "description"):
                field = re.search(rf"(?m)^{key}:\s*(\S[^\r\n]*)$", frontmatter.group(1))
                if not field or field.group(1).strip("\"' ") in ("", "null", "~"):
                    errors.append(f"SKILL.md missing nonempty frontmatter field: {key}")
                elif key == "name" and field.group(1).strip("\"' ") != "research-weekly-report":
                    errors.append("SKILL.md name must be research-weekly-report")
    for path in root.rglob("*.md"):
        if any(part in {".git", "dist", "private", "local-notes", "__pycache__", ".venv"} for part in path.relative_to(root).parts):
            continue
        errors.extend(local_link_errors(path, root))
    if skill.is_dir():
        for path in skill.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".yaml", ".yml", ".json"}:
                continue
            content = path.read_text(encoding="utf-8-sig")
            if PERSONAL_ABSOLUTE.search(content):
                errors.append(f"Personal absolute path in skill: {path.relative_to(root)}")
            if SCAFFOLD.search(content):
                errors.append(f"Unfilled scaffold marker in skill: {path.relative_to(root)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Project root; defaults to the script's repository")
    args = parser.parse_args(argv)
    try:
        errors = validate_project(args.root)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"Validation stopped: {error}\n")
    if errors:
        print("Structural validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Structure and local links passed. Content accuracy, privacy and skill behavior require human review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
