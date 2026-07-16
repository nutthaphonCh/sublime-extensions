from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable, List, Optional


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

