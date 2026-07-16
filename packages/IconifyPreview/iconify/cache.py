from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional, Union


class IconCache:
    def __init__(self, root: Union[str, Path]) -> None:
        self.root = Path(root)
        self.icons = self.root / "icons"
        self.searches = self.root / "search"
        self.icons.mkdir(parents=True, exist_ok=True)
        self.searches.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(*parts: object) -> str:
        value = "\0".join(str(part) for part in parts)
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def paths(self, icon: str, size: int, color: str) -> tuple[Path, Path]:
        stem = self.key(icon, size, color)
        return self.icons / f"{stem}.svg", self.icons / f"{stem}.png"

    def search_path(self, query: str, limit: int) -> Path:
        return self.searches / f"{self.key(query, limit)}.json"

    @staticmethod
    def atomic_write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def read_search(self, query: str, limit: int) -> Optional[list[str]]:
        path = self.search_path(query, limit)
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
            return None
        return payload

    def write_search(self, query: str, limit: int, icons: list[str]) -> None:
        self.atomic_write(
            self.search_path(query, limit),
            json.dumps(icons, separators=(",", ":")).encode("utf-8"),
        )
