from typing import Any, Optional

from mi_companion.layer_descriptors import OBSTACLES_GROUP_DESCRIPTOR
from mi_companion.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_current_parent,
)

__all__ = ["validate_obstacles_group_node"]


def validate_obstacles_group_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    """

    :param node:
    :param parent:
    :return:
    """
    return check_current_parent(node, OBSTACLES_GROUP_DESCRIPTOR, parent)
    # check_children(node, OBSTACLES_GROUP_DESCRIPTOR, parent)
