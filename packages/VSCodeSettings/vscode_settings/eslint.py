from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional


def find_command(
    root: Path,
    platform: str,
    which: Callable[[str], Optional[str]] = shutil.which,
) -> Optional[List[str]]:
    candidates = [root / "node_modules" / ".bin" / "eslint"]
    if platform == "windows":
        candidates.insert(0, root / "node_modules" / ".bin" / "eslint.cmd")
    for candidate in candidates:
        if candidate.is_file() and (
            os.access(str(candidate), os.X_OK) or candidate.suffix == ".cmd"
        ):
            return [str(candidate)]
    executable = which("eslint")
    return [executable] if executable else None


def find_node(
    platform: str,
    configured: str = "",
    which: Callable[[str], Optional[str]] = shutil.which,
    home: Optional[Path] = None,
    root: Optional[Path] = None,
) -> Optional[Path]:
    """Find Node even when Sublime was launched without the user's shell PATH."""
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_dir():
            candidate /= "node.exe" if platform == "windows" else "node"
        if candidate.is_file() and os.access(str(candidate), os.X_OK):
            return candidate

    executable = which("node")
    if executable:
        return Path(executable)

    if platform == "windows":
        return None

    home = home or Path.home()
    nvm_nodes = sorted(
        (home / ".nvm" / "versions" / "node").glob("*/bin/node"),
        key=_node_version_key,
        reverse=True,
    )
    requested = _requested_node_version(root, home)
    preferred_nvm = [
        node
        for node in nvm_nodes
        if requested and _version_matches(node.parents[1].name, requested)
    ]
    candidates = preferred_nvm + [
        Path("/opt/homebrew/bin/node"),
        Path("/usr/local/bin/node"),
        home / ".volta" / "bin" / "node",
        home / ".local" / "bin" / "node",
    ] + nvm_nodes
    patterns = [
        (home / ".local" / "share" / "mise" / "installs" / "node", "*/bin/node"),
        (home / ".fnm" / "node-versions", "*/installation/bin/node"),
    ]
    for base, pattern in patterns:
        candidates.extend(sorted(base.glob(pattern), reverse=True))

    return next(
        (
            candidate
            for candidate in candidates
            if candidate.is_file() and os.access(str(candidate), os.X_OK)
        ),
        None,
    )


def _requested_node_version(root: Optional[Path], home: Path) -> str:
    version_files = []
    if root is not None:
        version_files.extend([root / ".nvmrc", root / ".node-version"])
    version_files.append(home / ".nvm" / "alias" / "default")
    for version_file in version_files:
        try:
            version = version_file.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if re.fullmatch(r"v?\d+(?:\.\d+){0,2}", version):
            return version.lstrip("v")
    return ""


def _node_version_key(node: Path) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", node.parents[1].name))


def _version_matches(installed: str, requested: str) -> bool:
    installed = installed.lstrip("v")
    return installed == requested or installed.startswith(requested + ".")


def environment_with_node(
    platform: str,
    configured: str = "",
    environ: Optional[Mapping[str, str]] = None,
    which: Callable[[str], Optional[str]] = shutil.which,
    home: Optional[Path] = None,
    root: Optional[Path] = None,
) -> Dict[str, str]:
    environment = dict(os.environ if environ is None else environ)
    node = find_node(platform, configured, which=which, home=home, root=root)
    if node is None:
        return environment
    node_directory = str(node.parent)
    path = environment.get("PATH", "")
    entries = path.split(os.pathsep) if path else []
    if node_directory not in entries:
        environment["PATH"] = os.pathsep.join([node_directory] + entries)
    return environment
