from typing import Any, Optional

from mi_plugin.layer_descriptors import DOORS_GROUP_DESCRIPTOR
from mi_plugin.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_current_parent,
)

__all__ = ["validate_doors_group_node"]


def validate_doors_group_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    return check_current_parent(node, DOORS_GROUP_DESCRIPTOR, parent)
    # check_children(node, DOORS_GROUP_DESCRIPTOR, parent)
