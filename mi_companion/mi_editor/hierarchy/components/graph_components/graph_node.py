from typing import Any, Optional

from mi_companion.layer_descriptors import (
    GRAPH_BOUND_DESCRIPTOR,
    GRAPH_GROUP_DESCRIPTOR,
    GRAPH_LINES_DESCRIPTOR,
)
from mi_companion.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_children,
    check_current_parent,
    check_siblings_for_duplicates,
)

__all__ = [
    "validate_graph_group_node",
    "validate_graph_lines_layer_node",
    "validate_graph_bound_layer_node",
]


def validate_graph_group_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    """

    :param node:
    :param parent:
    :return:
    """
    for c in (check_current_parent, check_children, check_siblings_for_duplicates):
        reply = c(node, GRAPH_GROUP_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted


def validate_graph_bound_layer_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    """

    :param node:
    :param parent:
    :return:
    """
    for c in (check_current_parent, check_siblings_for_duplicates):
        reply = c(node, GRAPH_BOUND_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted


def validate_graph_lines_layer_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    for c in (check_current_parent, check_siblings_for_duplicates):
        reply = c(node, GRAPH_LINES_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted
