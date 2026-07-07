from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any


_SCALAR_TRUE = {"true", "yes", "on"}
_SCALAR_FALSE = {"false", "no", "off"}
_SCALAR_NULL = {"null", "none", "~"}


def _load_text(stream) -> str:
    if hasattr(stream, "read"):
        return stream.read()
    return str(stream)


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if not text:
        return ""
    if text.startswith(("'", '"')) and text.endswith(("'", '"')):
        return text[1:-1]
    lowered = text.lower()
    if lowered in _SCALAR_TRUE:
        return True
    if lowered in _SCALAR_FALSE:
        return False
    if lowered in _SCALAR_NULL:
        return None
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except Exception:
            pass
    if re.fullmatch(r"-?\d+\.\d+", text):
        try:
            return float(text)
        except Exception:
            pass
    return text


def _strip_comment(line: str) -> str:
    if "#" not in line:
        return line.rstrip()
    in_quote = None
    for index, char in enumerate(line):
        if char in {"'", '"'}:
            if in_quote is None:
                in_quote = char
            elif in_quote == char:
                in_quote = None
        elif char == "#" and in_quote is None:
            return line[:index].rstrip()
    return line.rstrip()


def safe_load(stream) -> Any:
    text = _load_text(stream)
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except Exception:
        pass

    lines = [_strip_comment(line) for line in text.splitlines()]
    lines = [line for line in lines if line.strip()]
    if not lines:
        return None

    anchors: dict[str, Any] = {}

    def parse_mapping(start_index: int, indent: int) -> tuple[dict[str, Any], int]:
        mapping: dict[str, Any] = {}
        index = start_index
        while index < len(lines):
            line = lines[index]
            current_indent = len(line) - len(line.lstrip(" "))
            if current_indent < indent:
                break
            if current_indent > indent:
                raise ValueError(f"Unexpected indentation in YAML shim: {line!r}")
            content = line[indent:]
            if ":" not in content:
                raise ValueError(f"Invalid YAML shim line: {line!r}")
            key, value = content.split(":", 1)
            key = key.strip()
            value = value.strip()
            index += 1
            if value == "":
                nested, index = parse_mapping(index, indent + 2)
                mapping[key] = nested
                continue
            if value.startswith("&"):
                anchor_name = value[1:].strip()
                nested, index = parse_mapping(index, indent + 2)
                mapping[key] = nested
                anchors[anchor_name] = nested
                continue
            if value.startswith("*"):
                anchor_name = value[1:].strip()
                mapping[key] = deepcopy(anchors.get(anchor_name, {}))
                continue
            if key == "<<" and value.startswith("*"):
                anchor_name = value[1:].strip()
                merged = deepcopy(anchors.get(anchor_name, {}))
                if not isinstance(merged, dict):
                    raise TypeError(f"YAML shim merge anchor {anchor_name!r} is not a mapping")
                mapping = {**merged, **mapping}
                continue
            mapping[key] = _parse_scalar(value)
        return mapping, index

    result, _ = parse_mapping(0, 0)
    return result


def safe_dump(data: Any, *args, **kwargs) -> str:
    return json.dumps(data, indent=2, sort_keys=True)
