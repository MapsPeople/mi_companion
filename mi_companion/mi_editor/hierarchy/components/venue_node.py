from typing import Any, Optional

from mi_companion.layer_descriptors import (
    VENUE_GROUP_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
)
from mi_companion.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_children,
    check_current_parent,
    check_siblings_for_duplicates,
)

__all__ = ["validate_venue_group_node", "validate_venue_polygon_layer_node"]


def validate_venue_group_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    for c in (check_current_parent, check_children):
        reply = c(node, VENUE_GROUP_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted


def validate_venue_polygon_layer_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    for c in (check_current_parent, check_siblings_for_duplicates):
        reply = c(node, VENUE_POLYGON_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted
