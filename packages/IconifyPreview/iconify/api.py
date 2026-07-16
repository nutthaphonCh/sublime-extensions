from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional


class IconifyError(RuntimeError):
    pass


class IconNotFound(IconifyError):
    pass


class IconifyAPI:
    def __init__(self, base_url: str = "https://api.iconify.design", timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, query: dict[str, object] | None = None) -> bytes:
        suffix = ""
        if query:
            suffix = "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(
            self.base_url + path + suffix,
            headers={"User-Agent": "Sublime-IconifyPreview/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise IconifyError(f"Iconify returned HTTP {response.status}")
                data = response.read(2_000_001)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise IconNotFound("Iconify icon not found") from error
            raise IconifyError(str(error)) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise IconifyError(str(error)) from error
        if len(data) > 2_000_000:
            raise IconifyError("Iconify response exceeded 2 MB")
        return data

    def svg(self, prefix: str, name: str, size: int, color: str) -> bytes:
        safe_prefix = urllib.parse.quote(prefix, safe="")
        safe_name = urllib.parse.quote(name, safe="")
        data = self._get(
            f"/{safe_prefix}/{safe_name}.svg",
            {"height": size, "color": color},
        )
        if b"<svg" not in data[:500].lower():
            raise IconifyError(f"{prefix}:{name} is not a valid Iconify icon")
        return data

    def search(self, query: str, limit: int = 50, prefix: Optional[str] = None) -> list[str]:
        params: dict[str, object] = {"query": query, "limit": limit}
        if prefix:
            params["prefix"] = prefix
        raw = self._get("/search", params)
        try:
            payload: Any = json.loads(raw.decode("utf-8"))
            icons = payload["icons"]
        except (UnicodeDecodeError, ValueError, KeyError, TypeError) as error:
            raise IconifyError("Invalid Iconify search response") from error
        if not isinstance(icons, list):
            raise IconifyError("Invalid Iconify search results")
        return [item for item in icons if isinstance(item, str)][:limit]
