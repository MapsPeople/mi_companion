from typing import Any, Optional

from mi_companion.layer_descriptors import ENTRY_POINTS_GROUP_DESCRIPTOR
from mi_companion.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_current_parent,
)

__all__ = ["validate_entry_points_group_node"]


def validate_entry_points_group_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    return check_current_parent(node, ENTRY_POINTS_GROUP_DESCRIPTOR, parent)
    # check_children(node, ENTRY_POINTS_GROUP_DESCRIPTOR, parent)
