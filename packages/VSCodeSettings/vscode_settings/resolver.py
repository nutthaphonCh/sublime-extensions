from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .jsonc import loads


_OVERRIDE_KEY = re.compile(r"^(?:\[[^\]]+\])+$")
_LANGUAGE_PART = re.compile(r"\[([^\]]+)\]")

_EXTENSION_LANGUAGES = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".go": "go",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".cjs": "javascript",
    ".mjs": "javascript",
    ".jsx": "javascriptreact",
    ".json": "json",
    ".jsonc": "jsonc",
    ".less": "less",
    ".md": "markdown",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".scss": "scss",
    ".svelte": "svelte",
    ".ts": "typescript",
    ".cts": "typescript",
    ".mts": "typescript",
    ".tsx": "typescriptreact",
    ".vue": "vue",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


@dataclass(frozen=True)
class ResolvedSettings:
    source: Path
    root: Path
    language: str
    values: Dict[str, Any]


class SettingsResolver:
    def __init__(self) -> None:
        self._cache: Dict[Path, Tuple[int, Dict[str, Any]]] = {}

    def clear(self) -> None:
        self._cache.clear()

    def resolve(self, filename: str) -> Optional[ResolvedSettings]:
        path = Path(filename).resolve()
        source = find_settings_file(path)
        if source is None:
            return None
        raw = self._read(source)
        language = language_id(path)
        return ResolvedSettings(
            source=source,
            root=source.parent.parent,
            language=language,
            values=effective_settings(raw, language),
        )

    def _read(self, source: Path) -> Dict[str, Any]:
        modified = source.stat().st_mtime_ns
        cached = self._cache.get(source)
        if cached is not None and cached[0] == modified:
            return cached[1]
        parsed = loads(source.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("workspace settings must be a JSON object")
        self._cache[source] = (modified, parsed)
        return parsed


def find_settings_file(path: Path) -> Optional[Path]:
    current = path if path.is_dir() else path.parent
    for directory in (current, *current.parents):
        candidate = directory / ".vscode" / "settings.json"
        if candidate.is_file():
            return candidate
    return None


def language_id(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".d.ts"):
        return "typescript"
    return _EXTENSION_LANGUAGES.get(path.suffix.lower(), "plaintext")


def effective_settings(raw: Dict[str, Any], language: str) -> Dict[str, Any]:
    result = {
        key: copy.deepcopy(value)
        for key, value in raw.items()
        if not _OVERRIDE_KEY.match(key)
    }
    for key, value in raw.items():
        if not _OVERRIDE_KEY.match(key) or not isinstance(value, dict):
            continue
        if language in _LANGUAGE_PART.findall(key):
            _deep_merge(result, value)
    return result


def _deep_merge(target: Dict[str, Any], override: Dict[str, Any]) -> None:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)

