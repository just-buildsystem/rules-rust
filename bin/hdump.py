#!/usr/bin/env python3

import json
import sys
from typing import Any, Dict, List, Union

JSON = Union[str, int, float, bool, None, Dict[str, 'JSON'], List['JSON']]


def is_simple(entry: JSON) -> bool:
    if isinstance(entry, list):
        return len(entry) == 0
    if isinstance(entry, dict):
        return len(entry) == 0
    return True


def is_short(entry: Any, indent: int) -> bool:
    return (len(json.dumps(entry)) + indent) < 80


def hdumps(entry: JSON, *, _current_indent: int = 0) -> str:
    if is_short(entry, _current_indent):
        return json.dumps(entry)
    if isinstance(entry, list) and entry:
        result: str = "[ " + hdumps(entry[0],
                                    _current_indent=_current_indent + 2)
        for x in entry[1:]:
            result += "\n" + " " * _current_indent + ", "
            result += hdumps(x, _current_indent=_current_indent + 2)
        result += "\n" + " " * _current_indent + "]"
        return result
    if isinstance(entry, dict) and entry:
        result: str = "{ "
        is_first: bool = True
        for k in entry.keys():
            if not is_first:
                result += "\n" + " " * _current_indent + ", "
            result += json.dumps(k) + ":"
            if is_simple(entry[k]):
                result += " " + json.dumps(entry[k])
            elif is_short(entry[k], _current_indent + len(json.dumps(k)) + 4):
                result += " " + json.dumps(entry[k])
            else:
                result += "\n" + " " * _current_indent + "  "
                result += hdumps(entry[k], _current_indent=_current_indent + 2)
            is_first = False
        result += "\n" + " " * _current_indent + "}"
        return result
    return json.dumps(entry)


if __name__ == "__main__":
    data = json.load(sys.stdin)
    print(hdumps(data))
