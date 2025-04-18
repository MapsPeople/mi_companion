from typing import Any, Optional

from mi_companion.layer_descriptors import (
    BUILDING_GROUP_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
)
from mi_companion.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_children,
    check_current_parent,
    check_siblings_for_duplicates,
)

__all__ = ["validate_building_group_node", "validate_building_polygon_layer_node"]


def validate_building_group_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    """

    :param node:
    :param parent:
    :return:
    """
    for c in (check_current_parent, check_children):
        reply = c(node, BUILDING_GROUP_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted


def validate_building_polygon_layer_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    """

    :param node:
    :param parent:
    :return:
    """
    for c in (check_current_parent, check_siblings_for_duplicates):
        reply = c(node, BUILDING_POLYGON_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted
