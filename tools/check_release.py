"""Validate the public release metadata before building or publishing."""
from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _string_constant(value: ast.AST) -> str | None:
    return value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None


def read_source_version() -> str:
    path = ROOT / "src" / "services" / "release_info_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSION":
                    value = _string_constant(node.value)
                    if value:
                        return value
    raise ValueError(f"Could not find a string VERSION assignment in {path}")


def read_installer_version() -> str:
    path = ROOT / "windows" / "installer.iss"
    match = re.search(r'^#define\s+AppVersion\s+"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find the default AppVersion in {path}")
    return match.group(1)


def validate(expected: str | None = None) -> str:
    source_version = read_source_version()
    installer_version = read_installer_version()
    if not SEMVER.fullmatch(source_version):
        raise ValueError(f"Source VERSION is not MAJOR.MINOR.PATCH: {source_version}")
    if source_version != installer_version:
        raise ValueError(
            f"Source VERSION {source_version} does not match installer default {installer_version}"
        )
    if expected and source_version != expected.removeprefix("v"):
        raise ValueError(f"Expected version {expected} does not match source VERSION {source_version}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "windows-release.yml").read_text(encoding="utf-8")
    required_readme_text = ("wgviptop", "wyTMBj6IuRBjN2U1", "github.com/zwang1790-debug/yutan/releases")
    missing = [value for value in required_readme_text if value not in readme]
    if missing:
        raise ValueError(f"README.md is missing public support links: {', '.join(missing)}")
    for marker in ("YuTanRadar-Setup-", "SHA256", "contents: write"):
        if marker not in workflow:
            raise ValueError(f"Windows release workflow is missing required marker: {marker}")
    return source_version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="Expected MAJOR.MINOR.PATCH version, with or without v")
    args = parser.parse_args()
    version = validate(args.version)
    print(f"Release metadata OK: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
