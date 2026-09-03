from __future__ import annotations

from typing import Any

_MISSING = object()


def get_path(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def matches(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    if "all" in condition:
        return all(matches(item, context) for item in condition["all"])
    if "any" in condition:
        return any(matches(item, context) for item in condition["any"])
    if "not" in condition:
        return not matches(condition["not"], context)

    actual = get_path(context, condition["path"])
    op = condition.get("op", "equals")
    expected = condition.get("value")

    if op == "exists":
        return (actual is not _MISSING) is bool(expected)
    if actual is _MISSING:
        return False
    if op == "equals":
        return actual == expected
    if op == "not_equals":
        return actual != expected
    if op == "in":
        return actual in expected
    if op == "not_in":
        return actual not in expected
    if op == "contains":
        return isinstance(actual, (list, tuple, set, str)) and expected in actual
    if op == "not_contains":
        return isinstance(actual, (list, tuple, set, str)) and expected not in actual
    if op == "contains_any":
        return isinstance(actual, (list, tuple, set)) and any(item in actual for item in expected)
    if op == "contains_all":
        return isinstance(actual, (list, tuple, set)) and all(item in actual for item in expected)
    if op == "is_null":
        return (actual is None) is bool(expected)
    if op == "before":
        return actual is not None and str(actual) < str(expected)
    if op == "on_or_after":
        return actual is not None and str(actual) >= str(expected)
    if op == "is_true":
        return actual is True
    if op == "is_false":
        return actual is False
    raise ValueError(f"Operador de condicion no soportado: {op}")
