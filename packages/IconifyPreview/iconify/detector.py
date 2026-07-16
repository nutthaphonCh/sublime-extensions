from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional


_COLON = re.compile(
    r"(?<![\w:-])@?(?P<prefix>[a-z][a-z0-9]*(?:-[a-z0-9]+)*):"
    r"(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)(?![\w-])",
    re.IGNORECASE,
)
_BRACKET = re.compile(
    r"(?<![\w-])(?:icon|i)-\[(?P<prefix>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)"
    r"--(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)\]",
    re.IGNORECASE,
)
_UNO = re.compile(
    r"(?<![\w-])i-(?P<identifier>[a-z][a-z0-9]*(?:-[a-z0-9]+)+)(?![\w-])",
    re.IGNORECASE,
)

_IGNORED_PREFIXES = frozenset(
    (
        # URI schemes that commonly occur in source files.
        "data",
        "file",
        "http",
        "https",
        "mailto",
        # Time formats and social/SEO metadata keys.
        "hh",
        "og",
        "tw",
        "twitter",
        # Tailwind responsive, state, and feature variants.
        "sm",
        "md",
        "lg",
        "xl",
        "2xl",
        "hover",
        "focus",
        "focus-within",
        "focus-visible",
        "active",
        "visited",
        "target",
        "first",
        "last",
        "only",
        "odd",
        "even",
        "disabled",
        "enabled",
        "checked",
        "required",
        "valid",
        "invalid",
        "read-only",
        "before",
        "after",
        "placeholder",
        "selection",
        "dark",
        "portrait",
        "landscape",
        "motion-safe",
        "motion-reduce",
        "print",
        "rtl",
        "ltr",
        "open",
        "group-hover",
        "group-focus",
        "peer-hover",
        "peer-focus",
        "peer-checked",
    )
)
_COMMON_HYPHENATED_PREFIXES = (
    "material-symbols-light",
    "material-symbols",
    "fluent-emoji-high-contrast",
    "fluent-emoji-flat",
    "fluent-emoji",
    "icon-park-outline",
    "icon-park-twotone",
    "icon-park-solid",
    "icon-park",
    "fa6-regular",
    "fa6-solid",
    "fa6-brands",
    "mdi-light",
    "line-md",
)


@dataclass(frozen=True)
class IconToken:
    prefix: str
    name: str
    start: int
    end: int
    source: str
    syntax: str

    @property
    def icon(self) -> str:
        return f"{self.prefix}:{self.name}"


def _tokens(pattern: re.Pattern[str], text: str, offset: int, syntax: str) -> Iterable[IconToken]:
    for match in pattern.finditer(text):
        prefix = match.group("prefix").lower()
        if prefix in _IGNORED_PREFIXES:
            continue
        yield IconToken(
            prefix=prefix,
            name=match.group("name").lower(),
            start=offset + match.start(),
            end=offset + match.end(),
            source=match.group(0),
            syntax=syntax,
        )


def _uno_tokens(text: str, offset: int) -> Iterable[IconToken]:
    for match in _UNO.finditer(text):
        identifier = match.group("identifier").lower()
        prefix = ""
        name = ""
        for candidate in _COMMON_HYPHENATED_PREFIXES:
            marker = candidate + "-"
            if identifier.startswith(marker):
                prefix = candidate
                name = identifier[len(marker) :]
                break
        if not prefix:
            prefix, _, name = identifier.partition("-")
        if not prefix or not name:
            continue
        yield IconToken(
            prefix=prefix,
            name=name,
            start=offset + match.start(),
            end=offset + match.end(),
            source=match.group(0),
            syntax="uno",
        )


def find_tokens(text: str, offset: int = 0) -> list[IconToken]:
    """Find supported Iconify names, removing overlaps by specificity."""
    candidates = [
        *_tokens(_BRACKET, text, offset, "bracket"),
        *_tokens(_COLON, text, offset, "colon"),
        *_uno_tokens(text, offset),
    ]
    candidates.sort(key=lambda token: (token.start, -(token.end - token.start)))

    found: list[IconToken] = []
    for token in candidates:
        if any(token.start < item.end and token.end > item.start for item in found):
            continue
        found.append(token)
    return sorted(found, key=lambda token: token.start)


def token_at(text: str, point: int, offset: int = 0) -> Optional[IconToken]:
    for token in find_tokens(text, offset):
        if token.start <= point <= token.end:
            return token
    return None
