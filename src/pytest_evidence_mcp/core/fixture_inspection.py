from collections import Counter
from typing import Any

# Lists at or below this size are always enumerated in full (path[0],
# path[1], ...) - there's no output-size problem to solve at that scale,
# so no reason to lose the extra detail by collapsing.
_COLLAPSE_THRESHOLD = 10


def inspect(data: Any) -> dict[str, Any]:
    """Recursively inspects already-parsed fixture data (dict/list/scalar).

    Returns field_count, null_fields and types, all keyed by leaf-only
    paths (e.g. "user.email", "orders[1].total"). Containers (dict/list)
    are never counted as fields themselves, except when empty - an empty
    container has no leaves to report, so it's recorded as a leaf of its
    own container type instead of silently disappearing from the report.

    Also returns collapsed_lists: paths of lists bigger than
    _COLLAPSE_THRESHOLD whose majority shape got folded into a single
    "path[]" entry to keep the output bounded, mapped to how many items
    were folded in. This is only safe because every folded item shares the
    exact same schema (same fields, same types) as the representative one
    reported. Items whose shape differs from the majority are still
    reported individually, with their real index - those are exactly the
    anomalies this kind of integrity check exists to surface, so they're
    never hidden by the collapsing.
    """
    types: dict[str, str] = {}
    null_fields: list[str] = []
    collapsed_lists: dict[str, int] = {}

    _walk(data, "", types, null_fields, collapsed_lists)

    return {
        "field_count": len(types),
        "null_fields": null_fields,
        "types": types,
        "collapsed_lists": collapsed_lists,
    }


def _walk(
    value: Any,
    path: str,
    types: dict[str, str],
    null_fields: list[str],
    collapsed_lists: dict[str, int],
) -> None:
    """Recursively walks value, recording one entry per leaf into types
    (and into null_fields when the leaf is None)."""

    if isinstance(value, dict):
        if not value:
            types[path] = "object"
            return
        for key, val in value.items():
            child_path = f"{path}.{key}" if path else key
            _walk(val, child_path, types, null_fields, collapsed_lists)
        return

    if isinstance(value, list):
        if not value:
            types[path] = "list"
            return
        if len(value) > _COLLAPSE_THRESHOLD:
            _walk_large_list(value, path, types, null_fields, collapsed_lists)
            return
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            _walk(item, child_path, types, null_fields, collapsed_lists)
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


def _signature_of(item: Any) -> frozenset[tuple[str, str]]:
    """Structural fingerprint of one list item: the set of (relative leaf
    path, type) pairs it would produce on its own. Two items with the same
    fingerprint are schema-identical - same fields, same types, same
    null-ness - and safe to collapse into a single representative entry.
    """
    temp_types: dict[str, str] = {}
    temp_nulls: list[str] = []
    temp_collapsed: dict[str, int] = {}
    _walk(item, "", temp_types, temp_nulls, temp_collapsed)
    return frozenset(temp_types.items())


def _walk_large_list(
    value: list[Any],
    path: str,
    types: dict[str, str],
    null_fields: list[str],
    collapsed_lists: dict[str, int],
) -> None:
    """Handles a list bigger than _COLLAPSE_THRESHOLD: collapses the
    majority shape into a single "path[]" entry, and reports any item
    whose shape differs from the majority individually, with its real
    index - those are the anomalies worth surfacing, never hidden.
    """
    signatures = [_signature_of(item) for item in value]
    majority_signature, majority_count = Counter(signatures).most_common(1)[0]

    if majority_count == 1:
        # No shape repeats at all - collapsing wouldn't save anything
        # meaningful and could hide the one item that matters, so fall
        # back to enumerating everything individually.
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            _walk(item, child_path, types, null_fields, collapsed_lists)
        return

    representative_index = signatures.index(majority_signature)
    _walk(
        value[representative_index],
        f"{path}[]",
        types,
        null_fields,
        collapsed_lists,
    )
    collapsed_lists[path] = majority_count

    for index, (item, signature) in enumerate(zip(value, signatures)):
        if signature != majority_signature:
            child_path = f"{path}[{index}]"
            _walk(item, child_path, types, null_fields, collapsed_lists)
