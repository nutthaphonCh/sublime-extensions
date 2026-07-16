#!/usr/bin/env python3
from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path
from typing import Iterable


PACKAGES = ("IconifyPreview", "VSCodeSettings")
EXCLUDED_PARTS = {"__pycache__", "tests"}
EXCLUDED_NAMES = {".DS_Store", ".gitignore", "package-metadata.json"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def included_files(package: Path) -> Iterable[Path]:
    for path in sorted(package.rglob("*")):
        relative = path.relative_to(package)
        if path.is_dir() or path.is_symlink():
            continue
        if EXCLUDED_PARTS.intersection(relative.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
            continue
        yield path


def build(package: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in included_files(package):
            archive.write(path, path.relative_to(package).as_posix())


def verify(package: Path, archive_path: Path) -> None:
    expected = {path.relative_to(package).as_posix() for path in included_files(package)}
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        if names != expected:
            missing = sorted(expected - names)
            extra = sorted(names - expected)
            raise RuntimeError(f"archive mismatch: missing={missing}, extra={extra}")
        if any(name.startswith(f"{package.name}/") for name in names):
            raise RuntimeError(f"{archive_path} contains an unwanted package root folder")
        for info in archive.infolist():
            if info.filename == "bin/macos-universal/resvg":
                mode = info.external_attr >> 16
                if not mode & stat.S_IXUSR:
                    raise RuntimeError("bundled resvg lost its executable bit")
        if package.name == "IconifyPreview" and ".no-sublime-package" not in names:
            raise RuntimeError("IconifyPreview must be installed unpacked")
        if ".python-version" not in names:
            raise RuntimeError(f"{package.name} is missing .python-version")
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"corrupt member in {archive_path}: {bad}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Sublime Text release assets")
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    output = args.output if args.output.is_absolute() else root / args.output
    for name in PACKAGES:
        package = root / "packages" / name
        destination = output / f"{name}.sublime-package"
        build(package, destination)
        verify(package, destination)
        print(f"built {destination} ({destination.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

