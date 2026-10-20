#!/usr/bin/env python3
"""Build allowlisted skill and project ZIP files without private working files."""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "research-weekly-report"
VERSION = "0.1.0"
PROJECT_FILES = {"README.md", "README.en.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", ".gitignore", ".gitattributes"}
PROJECT_DIRECTORIES = {"scripts", "tests", "evals", ".github"}
EXCLUDED_PARTS = {".git", "dist", "__pycache__", ".venv", ".pytest_cache", "private", "local-notes", "node_modules"}
ALLOWED_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".txt"}


def eligible(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if any(part.startswith(".env") for part in relative.parts):
        return False
    if path.is_symlink():
        raise ValueError(f"Symbolic links cannot be packaged: {relative}")
    if not path.is_file():
        return False
    return path.suffix in ALLOWED_SUFFIXES or path.name in PROJECT_FILES


def skill_files(root: Path) -> list[Path]:
    source = root / "skills" / SKILL_NAME
    if (root / "skills").is_symlink() or source.is_symlink():
        raise ValueError("The skills directory and source skill must not be symbolic links")
    if not (source / "SKILL.md").is_file():
        raise ValueError(f"Missing skill entry point: {source / 'SKILL.md'}")
    return sorted(path for path in source.rglob("*") if eligible(path, root))


def project_files(root: Path, selected_skill_files: list[Path]) -> list[Path]:
    selected = set(selected_skill_files)
    for name in PROJECT_FILES:
        path = root / name
        if path.exists() and eligible(path, root):
            selected.add(path)
    for name in PROJECT_DIRECTORIES:
        directory = root / name
        if directory.is_symlink():
            raise ValueError(f"Symbolic links cannot be packaged: {name}")
        if directory.is_dir():
            selected.update(path for path in directory.rglob("*") if eligible(path, root))
    return sorted(selected)


def write_archive(destination: Path, files: list[Path], source_root: Path, prefix: str) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(source_root)
            if path.is_symlink() or not path.resolve().is_relative_to(source_root.resolve()):
                raise ValueError(f"Unsafe archive source: {relative}")
            archive.write(path, (Path(prefix) / relative).as_posix())


def package_project(root: Path, output_dir: Path) -> tuple[Path, Path]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    selected_skill_files = skill_files(root)
    selected_project_files = project_files(root, selected_skill_files)
    output_dir.mkdir(parents=True, exist_ok=True)
    skill_archive = output_dir / f"{SKILL_NAME}-v{VERSION}.zip"
    project_archive = output_dir / f"{SKILL_NAME}-project-v{VERSION}.zip"
    write_archive(skill_archive, selected_skill_files, root / "skills" / SKILL_NAME, SKILL_NAME)
    write_archive(project_archive, selected_project_files, root, "research-weekly-report-skill")
    return skill_archive, project_archive


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "dist", help="ZIP output folder")
    args = parser.parse_args(argv)
    try:
        archives = package_project(PROJECT_ROOT, args.output_dir)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Packaging stopped: {error}\n")
    for archive in archives:
        print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
