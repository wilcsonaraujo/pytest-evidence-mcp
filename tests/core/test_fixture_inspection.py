from pytest_evidence_mcp.core.fixture_inspection import inspect


def test_flat_object_counts_each_leaf():
    result = inspect({"name": "Alice", "age": 30})

    assert result["field_count"] == 2
    assert result["types"] == {"name": "string", "age": "integer"}
    assert result["null_fields"] == []


def test_nested_object_builds_dotted_path():
    result = inspect({"user": {"name": "Alice", "email": None}})

    assert result["field_count"] == 2
    assert result["types"]["user.name"] == "string"
    assert result["types"]["user.email"] == "null"
    assert result["null_fields"] == ["user.email"]


def test_null_in_place_of_container_is_a_leaf():
    """"address" would normally be an object, but came as null - it must
    still be counted/typed, not silently skipped for lack of children."""
    result = inspect({"address": None})

    assert result["field_count"] == 1
    assert result["types"]["address"] == "null"
    assert result["null_fields"] == ["address"]


def test_list_of_scalars_recurses_into_each_item():
    result = inspect({"tags": ["a", "b", "c"]})

    assert result["field_count"] == 3
    assert result["types"] == {
        "tags[0]": "string",
        "tags[1]": "string",
        "tags[2]": "string",
    }


def test_list_of_dicts_recurses_into_each_items_fields():
    result = inspect({"orders": [{"id": 1, "total": 10.5}, {"id": 2, "total": None}]})

    assert result["field_count"] == 4
    assert result["types"]["orders[0].id"] == "integer"
    assert result["types"]["orders[1].total"] == "null"
    assert result["null_fields"] == ["orders[1].total"]


def test_empty_list_is_recorded_but_not_null():
    result = inspect({"tags": []})

    assert result["field_count"] == 1
    assert result["types"]["tags"] == "list"
    assert result["null_fields"] == []


def test_empty_dict_is_recorded_but_not_null():
    result = inspect({"metadata": {}})

    assert result["field_count"] == 1
    assert result["types"]["metadata"] == "object"
    assert result["null_fields"] == []


def test_containers_themselves_are_never_counted():
    """Same 2 real values, one flat and one wrapped in a container - the
    count must be the same, because containers aren't fields."""
    flat = inspect({"name": "Alice", "age": 30})
    nested = inspect({"user": {"name": "Alice", "age": 30}})

    assert flat["field_count"] == nested["field_count"] == 2


def test_small_list_of_dicts_is_never_collapsed():
    """At or below the threshold, every item is enumerated individually -
    no output-size problem to solve at that scale."""
    orders = [{"id": i, "total": 10.0} for i in range(10)]
    result = inspect({"orders": orders})

    assert result["collapsed_lists"] == {}
    assert result["types"]["orders[0].id"] == "integer"
    assert result["types"]["orders[9].id"] == "integer"


def test_large_uniform_list_collapses_to_single_entry():
    orders = [{"id": i, "total": 10.0} for i in range(50)]
    result = inspect({"orders": orders})

    assert result["collapsed_lists"] == {"orders": 50}
    assert result["types"] == {"orders[].id": "integer", "orders[].total": "float"}


def test_large_list_with_anomaly_keeps_outlier_visible():
    """49 identical records collapse into one entry; the one record with a
    different shape at "total" (string instead of float) is exactly the
    kind of anomaly this tool exists to surface, so it must stay visible
    with its real index instead of being folded away."""
    orders = [{"id": i, "total": 10.0} for i in range(50)]
    orders[23]["total"] = "not-a-number"

    result = inspect({"orders": orders})

    assert result["collapsed_lists"] == {"orders": 49}
    assert result["types"]["orders[].id"] == "integer"
    assert result["types"]["orders[].total"] == "float"
    # the whole anomalous record is reported, not just the field that
    # diverges - full context on the one item worth looking at
    assert result["types"]["orders[23].id"] == "integer"
    assert result["types"]["orders[23].total"] == "string"


def test_large_list_with_no_repeating_shape_enumerates_everything():
    """No two items share a shape at all - collapsing would save nothing
    and risks hiding the one item that matters, so every item is reported
    individually, same as a small list."""
    orders = [{f"field_{i}": i} for i in range(20)]

    result = inspect({"orders": orders})

    assert result["collapsed_lists"] == {}
    assert result["field_count"] == 20
