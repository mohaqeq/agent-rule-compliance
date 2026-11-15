import ast
import inspect
import textwrap

from .. import utils as channel_utils

FUNCTION_NAME = "get_warehouse_ids_by_channel"


def _function_tree():
    function = getattr(channel_utils, FUNCTION_NAME)
    return ast.parse(textwrap.dedent(inspect.getsource(function)))


def test_rule_helper_does_not_read_the_id_attribute():
    """Model instances are referenced by pk, not by the id field."""
    # given
    tree = _function_tree()

    # when
    id_attributes = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "id"
    ]

    # then
    assert id_attributes == []


def test_rule_helper_does_not_use_the_id_field_in_queries():
    """Querysets refer to pk, pk__in and order_by("pk"), never to id."""
    # given
    tree = _function_tree()
    id_lookups = []

    # when
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg:
            if node.arg == "id" or node.arg.startswith("id__"):
                id_lookups.append(node.arg)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in {"id", "-id"} or node.value.startswith("id__"):
                id_lookups.append(node.value)

    # then
    assert id_lookups == []
