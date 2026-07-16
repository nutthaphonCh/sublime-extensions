from __future__ import annotations

import importlib
import subprocess
import threading
from pathlib import Path
from typing import Dict, Set

import sublime
import sublime_plugin

from .vscode_settings import eslint as _eslint_module
from .vscode_settings import jsonc as _jsonc_module
from .vscode_settings import mappings as _mappings_module
from .vscode_settings import resolver as _resolver_module


# Sublime reloads plugin entrypoints after a Package Control upgrade, but may
# retain imported package modules. Reload them so new entrypoints never bind to
# stale helpers from the previous installed version.
_jsonc_module = importlib.reload(_jsonc_module)
_eslint_module = importlib.reload(_eslint_module)
_mappings_module = importlib.reload(_mappings_module)
_resolver_module = importlib.reload(_resolver_module)

environment_with_node = _eslint_module.environment_with_node
find_command = _eslint_module.find_command
eslint_fix_requested = _mappings_module.eslint_fix_requested
sublime_settings = _mappings_module.sublime_settings
ResolvedSettings = _resolver_module.ResolvedSettings
SettingsResolver = _resolver_module.SettingsResolver


SETTINGS_FILE = "VSCodeSettings.sublime-settings"
STATUS_KEY = "vscode_settings.source"

_resolver = SettingsResolver()
_applied: Dict[int, Set[str]] = {}
_resolved: Dict[int, ResolvedSettings] = {}
_eslint_running: Set[str] = set()
_eslint_lock = threading.Lock()


def _package_settings() -> sublime.Settings:
    return sublime.load_settings(SETTINGS_FILE)


def plugin_loaded() -> None:
    reload_all()


def plugin_unloaded() -> None:
    for window in sublime.windows():
        for view in window.views():
            _clear_view(view)


def reload_all() -> None:
    _resolver.clear()
    for window in sublime.windows():
        for view in window.views():
            apply_to_view(view)


def apply_to_view(view: sublime.View) -> None:
    if not view.is_valid() or not bool(_package_settings().get("enabled", True)):
        _clear_view(view)
        return
    filename = view.file_name()
    if not filename:
        _clear_view(view)
        return
    try:
        resolved = _resolver.resolve(filename)
    except Exception as error:
        _clear_view(view)
        print(f"VSCodeSettings: {filename}: {error}")
        view.set_status(STATUS_KEY, ".vscode settings: invalid JSONC")
        return
    if resolved is None:
        _clear_view(view)
        return

    mapped = sublime_settings(resolved.values)
    previous = _applied.get(view.id(), set())
    for key in previous - set(mapped):
        view.settings().erase(key)
    for key, value in mapped.items():
        view.settings().set(key, value)
    _applied[view.id()] = set(mapped)
    _resolved[view.id()] = resolved
    view.settings().set("vscode_settings.source", str(resolved.source))
    view.settings().set("vscode_settings.language", resolved.language)
    if bool(_package_settings().get("show_status", True)):
        view.set_status(STATUS_KEY, f".vscode: {resolved.root.name} [{resolved.language}]")
    else:
        view.erase_status(STATUS_KEY)


def _clear_view(view: sublime.View) -> None:
    for key in _applied.pop(view.id(), set()):
        view.settings().erase(key)
    _resolved.pop(view.id(), None)
    view.settings().erase("vscode_settings.source")
    view.settings().erase("vscode_settings.language")
    view.erase_status(STATUS_KEY)


class VSCodeSettingsListener(sublime_plugin.EventListener):
    def on_load_async(self, view: sublime.View) -> None:
        apply_to_view(view)

    def on_activated_async(self, view: sublime.View) -> None:
        apply_to_view(view)

    def on_post_save_async(self, view: sublime.View) -> None:
        filename = view.file_name()
        if not filename:
            return
        if Path(filename).as_posix().endswith("/.vscode/settings.json"):
            sublime.set_timeout_async(reload_all, 0)
            return
        apply_to_view(view)
        resolved = _resolved.get(view.id())
        if resolved is not None:
            _run_eslint_fix(view, resolved)

    def on_close(self, view: sublime.View) -> None:
        _applied.pop(view.id(), None)
        _resolved.pop(view.id(), None)


def _run_eslint_fix(view: sublime.View, resolved: ResolvedSettings) -> None:
    package = _package_settings()
    if not bool(package.get("eslint_fix_on_save", True)):
        return
    if not eslint_fix_requested(resolved.values):
        return
    filename = view.file_name()
    if not filename:
        return
    extensions = package.get("eslint_extensions", [])
    if Path(filename).suffix.lower() not in extensions:
        return
    command = find_command(resolved.root, sublime.platform())
    if command is None:
        print(f"VSCodeSettings: no ESLint executable found under {resolved.root}")
        return

    with _eslint_lock:
        if filename in _eslint_running:
            return
        _eslint_running.add(filename)

    change_count = view.change_count()
    try:
        before = Path(filename).read_bytes()
    except OSError:
        before = b""
    timeout = max(1, int(package.get("eslint_timeout", 30)))
    environment = environment_with_node(
        sublime.platform(), str(package.get("node_path", "")), root=resolved.root
    )

    def execute() -> None:
        try:
            result = subprocess.run(
                command + ["--fix", filename],
                cwd=str(resolved.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
                text=True,
                env=environment,
            )
            after = Path(filename).read_bytes()
            if result.returncode not in (0, 1):
                output = result.stdout.strip()[-2000:]
                print(f"VSCodeSettings: ESLint failed for {filename}\n{output}")
                sublime.set_timeout(
                    lambda: sublime.status_message("ESLint fix failed; see console"), 0
                )
            elif after != before:
                sublime.set_timeout(lambda: _reload_after_fix(view, change_count), 0)
        except Exception as error:
            print(f"VSCodeSettings: ESLint fix failed for {filename}: {error}")
            sublime.set_timeout(
                lambda: sublime.status_message("ESLint fix failed; see console"), 0
            )
        finally:
            with _eslint_lock:
                _eslint_running.discard(filename)

    threading.Thread(target=execute, name="vscode-settings-eslint", daemon=True).start()


def _reload_after_fix(view: sublime.View, change_count: int) -> None:
    if not view.is_valid() or view.is_dirty() or view.change_count() != change_count:
        sublime.status_message("ESLint fixed the file on disk; reload to apply")
        return
    view.run_command("revert")
    sublime.status_message("ESLint fixes applied from .vscode settings")


class VSCodeSettingsReloadCommand(sublime_plugin.ApplicationCommand):
    def run(self) -> None:
        reload_all()
        sublime.status_message("Reloaded .vscode workspace settings")


class VSCodeSettingsShowSourceCommand(sublime_plugin.TextCommand):
    def run(self, edit) -> None:
        resolved = _resolved.get(self.view.id())
        if resolved is None:
            sublime.message_dialog("No .vscode/settings.json applies to this file.")
            return
        sublime.message_dialog(
            "VS Code settings source:\n{}\n\nLanguage override: {}".format(
                resolved.source, resolved.language
            )
        )
