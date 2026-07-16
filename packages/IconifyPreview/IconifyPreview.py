from __future__ import annotations

import html
import re
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional

import sublime
import sublime_plugin

from .iconify.api import IconifyAPI
from .iconify.cache import IconCache
from .iconify.detector import IconToken, find_tokens, token_at
from .iconify.renderer import IconRenderer


PACKAGE = "IconifyPreview"
SETTINGS_FILE = "IconifyPreview.sublime-settings"
PHANTOM_KEY = "iconify_preview.inline"

_executor: Optional[ThreadPoolExecutor] = None
_service: Optional["IconService"] = None
_phantoms: dict[int, sublime.PhantomSet] = {}
_generations: dict[int, int] = {}


def _settings() -> sublime.Settings:
    return sublime.load_settings(SETTINGS_FILE)


def _setting(view: sublime.View, name: str, default=None):
    project_value = view.settings().get(f"iconify_preview.{name}")
    if project_value is not None:
        return project_value
    return _settings().get(name, default)


def _enabled(view: sublime.View) -> bool:
    if not bool(_setting(view, "enabled", True)):
        return False
    selector = str(_setting(view, "selector", "source, text.html, text.css"))
    return view.match_selector(0, selector) or any(view.match_selector(point, selector) for point in view.sel())


def _preview_color(view: sublime.View) -> str:
    configured = str(_setting(view, "color", "auto"))
    if configured != "auto":
        return configured
    try:
        color = view.style_for_scope("source").get("foreground")
    except Exception:
        color = None
    return color if isinstance(color, str) and color.startswith("#") else "#808080"


class IconService:
    def __init__(self) -> None:
        global _executor
        _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="iconify-preview")
        cache = IconCache(Path(sublime.cache_path()) / PACKAGE)
        settings = _settings()
        api = IconifyAPI(
            str(settings.get("api_url", "https://api.iconify.design")),
            float(settings.get("request_timeout", 5.0)),
        )
        self.cache = cache
        self.api = api
        self.renderer = IconRenderer(cache, api)
        self.executor = _executor
        self._lock = threading.Lock()
        self._renders: dict[tuple[str, int, str], Future[Path]] = {}

    def render(self, icon: str, size: int, color: str, callback: Callable[[Optional[Path]], None]) -> None:
        key = (icon, size, color)
        with self._lock:
            future = self._renders.get(key)
            if future is None:
                future = self.executor.submit(self.renderer.render, icon, size, color)
                self._renders[key] = future

        def done(result: Future[Path]) -> None:
            with self._lock:
                self._renders.pop(key, None)
            try:
                path: Optional[Path] = result.result()
            except Exception as error:
                print(f"IconifyPreview: {icon}: {error}")
                path = None
            sublime.set_timeout(lambda: callback(path), 0)

        future.add_done_callback(done)

    def search(self, query: str, prefix: str, limit: int) -> list[str]:
        cache_key = f"{prefix}:{query}"
        cached = self.cache.read_search(cache_key, limit)
        if cached is not None:
            return cached
        icons = self.api.search(query, limit, prefix)
        self.cache.write_search(cache_key, limit, icons)
        return icons


def plugin_loaded() -> None:
    global _service
    _service = IconService()
    for window in sublime.windows():
        for view in window.views():
            schedule_scan(view, immediate=True)


def plugin_unloaded() -> None:
    global _executor, _service
    for phantom_set in _phantoms.values():
        phantom_set.update([])
    _phantoms.clear()
    if _executor is not None:
        _executor.shutdown(wait=False)
    _executor = None
    _service = None


def schedule_scan(view: sublime.View, immediate: bool = False) -> None:
    if not view.is_valid():
        return
    view_id = view.id()
    generation = _generations.get(view_id, 0) + 1
    _generations[view_id] = generation
    delay = 0 if immediate else int(_setting(view, "debounce_ms", 250))

    def run() -> None:
        if _generations.get(view_id) == generation and view.is_valid():
            scan_view(view, generation)

    sublime.set_timeout_async(run, delay)


def scan_view(view: sublime.View, generation: int) -> None:
    if _service is None or not _enabled(view) or not bool(_setting(view, "inline_preview", True)):
        sublime.set_timeout(lambda: _update_phantoms(view, []), 0)
        return

    visible = view.visible_region()
    text = view.substr(visible)
    maximum = max(1, int(_setting(view, "max_inline_previews", 100)))
    tokens = find_tokens(text, visible.begin())[:maximum]
    if not tokens:
        sublime.set_timeout(lambda: _update_phantoms(view, []), 0)
        return

    size = max(12, min(64, int(_setting(view, "inline_size", 18))))
    color = _preview_color(view)
    ready: dict[tuple[int, int], Path] = {}
    def rendered(token: IconToken, path: Optional[Path]) -> None:
        if path is not None:
            ready[(token.start, token.end)] = path
        if _generations.get(view.id()) == generation and view.is_valid():
            phantoms = [
                _inline_phantom(token, ready[(token.start, token.end)])
                for token in tokens
                if (token.start, token.end) in ready
            ]
            _update_phantoms(view, phantoms)

    for token in tokens:
        _service.render(token.icon, size, color, lambda path, token=token: rendered(token, path))


def _inline_phantom(token: IconToken, path: Path) -> sublime.Phantom:
    label = html.escape(token.icon, quote=True)
    content = (
        "<body><style>body{margin:0 0 0 0.35rem}</style>"
        f'<img src="{path.as_uri()}" title="{label}"></body>'
    )
    return sublime.Phantom(sublime.Region(token.end, token.end), content, sublime.LAYOUT_INLINE)


def _update_phantoms(view: sublime.View, items: list[sublime.Phantom]) -> None:
    if not view.is_valid():
        return
    phantom_set = _phantoms.get(view.id())
    if phantom_set is None:
        phantom_set = sublime.PhantomSet(view, PHANTOM_KEY)
        _phantoms[view.id()] = phantom_set
    phantom_set.update(items)


def _token_near(view: sublime.View, point: int) -> Optional[IconToken]:
    line = view.line(point)
    return token_at(view.substr(line), point, line.begin())


class IconifyPreviewListener(sublime_plugin.EventListener):
    def on_load_async(self, view: sublime.View) -> None:
        schedule_scan(view, immediate=True)

    def on_activated_async(self, view: sublime.View) -> None:
        schedule_scan(view, immediate=True)

    def on_modified_async(self, view: sublime.View) -> None:
        schedule_scan(view)

    def on_close(self, view: sublime.View) -> None:
        _generations.pop(view.id(), None)
        _phantoms.pop(view.id(), None)

    def on_hover(self, view: sublime.View, point: int, hover_zone: int) -> None:
        if (
            _service is None
            or hover_zone != sublime.HOVER_TEXT
            or not _enabled(view)
            or not bool(_setting(view, "hover_preview", True))
        ):
            return
        token = _token_near(view, point)
        if token is None:
            return
        size = max(32, min(256, int(_setting(view, "hover_size", 96))))
        color = _preview_color(view)

        def show(path: Optional[Path]) -> None:
            if path is None or not view.is_valid():
                return
            current = _token_near(view, point)
            if current is None or current.icon != token.icon:
                return
            label = html.escape(token.icon, quote=True)
            href = f"https://icon-sets.iconify.design/{token.prefix}/{token.name}/"
            body = (
                "<body><style>body{padding:0.7rem;text-align:center}"
                "p{margin:0.4rem 0 0 0}</style>"
                f'<img src="{path.as_uri()}"><p><a href="{href}"><code>{label}</code></a></p></body>'
            )
            view.show_popup(body, location=point, max_width=size + 80, max_height=size + 80)

        _service.render(token.icon, size, color, show)

    def on_query_completions(self, view: sublime.View, prefix: str, locations: list[int]):
        if (
            _service is None
            or not locations
            or not _enabled(view)
            or not bool(_setting(view, "completions", True))
        ):
            return None
        point = locations[0]
        before = view.substr(sublime.Region(max(0, point - 160), point))
        context = _completion_context(before)
        if context is None:
            return None
        icon_prefix, query, closing_bracket = context
        if len(query) < int(_setting(view, "completion_min_chars", 2)):
            return None

        completion_list = sublime.CompletionList()
        limit = max(1, min(200, int(_setting(view, "completion_limit", 50))))

        def search() -> None:
            try:
                icons = _service.search(query, icon_prefix, limit) if _service is not None else []
            except Exception as error:
                print(f"IconifyPreview completion: {error}")
                icons = []
            values = []
            for icon in icons:
                result_prefix, _, name = icon.partition(":")
                if result_prefix != icon_prefix or not name:
                    continue
                insertion = name + ("]" if closing_bracket else "")
                values.append(
                    sublime.CompletionItem(
                        trigger=name,
                        annotation=f"Iconify · {result_prefix}",
                        completion=insertion,
                        kind=sublime.KIND_MARKUP,
                        details=html.escape(icon),
                    )
                )
            completion_list.set_completions(
                values,
                sublime.INHIBIT_WORD_COMPLETIONS | sublime.DYNAMIC_COMPLETIONS,
            )

        _service.executor.submit(search)
        return completion_list


_COLON_COMPLETION = re.compile(
    r"(?P<prefix>[a-z0-9]+(?:-[a-z0-9]+)*):(?P<query>[a-z0-9-]*)$",
    re.IGNORECASE,
)
_BRACKET_COMPLETION = re.compile(
    r"(?:icon|i)-\[(?P<prefix>[a-z0-9]+(?:-[a-z0-9]+)*)--(?P<query>[a-z0-9-]*)$",
    re.IGNORECASE,
)


def _completion_context(before: str) -> Optional[tuple[str, str, bool]]:
    bracket = _BRACKET_COMPLETION.search(before)
    if bracket:
        return bracket.group("prefix").lower(), bracket.group("query").lower(), True
    colon = _COLON_COMPLETION.search(before)
    if colon:
        return colon.group("prefix").lower(), colon.group("query").lower(), False
    return None


class IconifyPreviewRefreshCommand(sublime_plugin.TextCommand):
    def run(self, edit) -> None:
        schedule_scan(self.view, immediate=True)
        sublime.status_message("Iconify previews refreshed")


class IconifyPreviewToggleCommand(sublime_plugin.TextCommand):
    def run(self, edit) -> None:
        key = "iconify_preview.enabled"
        current = self.view.settings().get(key)
        if current is None:
            current = bool(_settings().get("enabled", True))
        self.view.settings().set(key, not current)
        schedule_scan(self.view, immediate=True)
        sublime.status_message(
            f"Iconify previews {'enabled' if not current else 'disabled'} for this view"
        )
