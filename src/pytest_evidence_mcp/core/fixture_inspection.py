from typing import Any


def inspect(data: Any) -> dict[str, Any]:
    """Recursively inspects already-parsed fixture data (dict/list/scalar).

    Returns field_count, null_fields and types, all keyed by leaf-only
    paths (e.g. "user.email", "orders[1].total"). Containers (dict/list)
    are never counted as fields themselves, except when empty - an empty
    container has no leaves to report, so it's recorded as a leaf of its
    own container type instead of silently disappearing from the report.
    """
    types: dict[str, str] = {}
    null_fields: list[str] = []

    _walk(data, "", types, null_fields)

    return {
        "field_count": len(types),
        "null_fields": null_fields,
        "types": types,
    }

def _walk(
    value: Any,
    path: str,
    types: dict[str, str],
    null_fields: list[str],
) -> None:
    """Recursively walks value, recording one entry per leaf into types
    (and into null_fields when the leaf is None)."""

    if isinstance(value, dict):
        if not value:
            types[path] = "object"
            return
        for key, val in value.items():
            child_path = f"{path}.{key}" if path else key
            _walk(val, child_path, types, null_fields)
        return

    if isinstance(value, list):
        if not value:
            types[path] = "list"
            return
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            _walk(item, child_path, types, null_fields)
        return

    if value is None:
        types[path] = "null"
        null_fields.append(path)
        return

    if isinstance(value, bool):
        types[path] = "boolean"
    elif isinstance(value, int):
        types[path] = "integer"
    elif isinstance(value, float):
        types[path] = "float"
    elif isinstance(value, str):
        types[path] = "string"
    else:
        types[path] = type(value).__name__
