from __future__ import annotations

from typing import Any, Dict, Iterable


def sublime_settings(values: Dict[str, Any]) -> Dict[str, Any]:
    mapped: Dict[str, Any] = {}
    _copy(values, mapped, "editor.tabSize", "tab_size", int, _positive_int)
    _copy(values, mapped, "editor.insertSpaces", "translate_tabs_to_spaces", bool, _is_bool)
    _copy(values, mapped, "editor.detectIndentation", "detect_indentation", bool, _is_bool)
    _copy(values, mapped, "editor.wordWrapColumn", "wrap_width", int, _positive_int)
    _copy(values, mapped, "files.trimTrailingWhitespace", "trim_trailing_white_space_on_save", bool, _is_bool)
    _copy(values, mapped, "files.insertFinalNewline", "ensure_newline_at_eof_on_save", bool, _is_bool)

    word_wrap = values.get("editor.wordWrap")
    if word_wrap in ("on", "bounded"):
        mapped["word_wrap"] = True
    elif word_wrap == "off":
        mapped["word_wrap"] = False

    whitespace = values.get("editor.renderWhitespace")
    if whitespace == "all":
        mapped["draw_white_space"] = "all"
    elif whitespace == "none":
        mapped["draw_white_space"] = "none"
    elif whitespace in ("boundary", "selection", "trailing"):
        mapped["draw_white_space"] = "selection"

    rulers = _rulers(values.get("editor.rulers"))
    if rulers is not None:
        mapped["rulers"] = rulers

    return mapped


def eslint_fix_requested(values: Dict[str, Any]) -> bool:
    actions = values.get("editor.codeActionsOnSave")
    request: Any = None
    if isinstance(actions, dict):
        request = actions.get("source.fixAll.eslint")
    if request is None:
        request = values.get("editor.codeActionsOnSave.source.fixAll.eslint")
    return request is True or request in ("explicit", "always")


def _copy(
    source: Dict[str, Any],
    target: Dict[str, Any],
    source_key: str,
    target_key: str,
    convert,
    valid,
) -> None:
    value = source.get(source_key)
    if valid(value):
        target[target_key] = convert(value)


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _rulers(value: Any):
    if not isinstance(value, list):
        return None
    result = []
    for item in value:
        column = item.get("column") if isinstance(item, dict) else item
        if _positive_int(column):
            result.append(column)
    return result

