#!/usr/bin/env python3
"""Install only the bundled skill, refusing to replace an existing target."""
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "research-weekly-report"


def default_skills_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / "skills"


def install_skill(source: Path, skills_dir: Path) -> Path:
    source = source.resolve()
    skills_dir = skills_dir.expanduser().resolve()
    target = skills_dir / SKILL_NAME
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"Target already exists; left unchanged: {target}")
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        raise ValueError(f"Source is not a skill directory: {source}")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("Skill source must not contain symbolic links")
    if source == skills_dir or source in skills_dir.parents:
        raise ValueError("Install destination must be outside the source skill")
    skills_dir.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}-", dir=skills_dir))
    try:
        staged = temporary / SKILL_NAME
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".git", "dist"))
        # Recheck immediately before rename; the existing target is never removed.
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Target already exists; left unchanged: {target}")
        staged.rename(target)
    finally:
        if not temporary.resolve().is_relative_to(skills_dir) or not temporary.name.startswith(f".{SKILL_NAME}-"):
            raise ValueError("Refusing to clean a temporary path outside the installation directory")
        shutil.rmtree(temporary)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, default=None, help="Parent directory that will contain the installed skill")
    args = parser.parse_args(argv)
    try:
        target = install_skill(PROJECT_ROOT / "skills" / SKILL_NAME, args.skills_dir or default_skills_dir())
    except (OSError, ValueError) as error:
        parser.exit(1, f"Installation stopped: {error}\n")
    print(f"Installed skill: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
