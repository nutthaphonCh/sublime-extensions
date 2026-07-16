from __future__ import annotations

import json
from typing import Any


def loads(source: str) -> Any:
    """Parse VS Code's JSON-with-comments settings format."""
    return json.loads(_strip_trailing_commas(_strip_comments(source)))


def _strip_comments(source: str) -> str:
    output = []
    index = 0
    in_string = False
    escaped = False
    length = len(source)

    while index < length:
        char = source[index]
        next_char = source[index + 1] if index + 1 < length else ""

        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue

        if char == "/" and next_char == "/":
            output.extend((" ", " "))
            index += 2
            while index < length and source[index] not in "\r\n":
                output.append(" ")
                index += 1
            continue

        if char == "/" and next_char == "*":
            output.extend((" ", " "))
            index += 2
            while index < length:
                if source[index] == "*" and index + 1 < length and source[index + 1] == "/":
                    output.extend((" ", " "))
                    index += 2
                    break
                output.append("\n" if source[index] == "\n" else " ")
                index += 1
            continue

        output.append(char)
        index += 1

    return "".join(output)


def _strip_trailing_commas(source: str) -> str:
    output = []
    index = 0
    in_string = False
    escaped = False

    while index < len(source):
        char = source[index]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
        elif char == ",":
            lookahead = index + 1
            while lookahead < len(source) and source[lookahead].isspace():
                lookahead += 1
            if lookahead < len(source) and source[lookahead] in "}]":
                index += 1
                continue
        output.append(char)
        index += 1

    return "".join(output)
