from typing import Any, Optional

from mi_companion.layer_descriptors import POINT_OF_INTERESTS_DESCRIPTOR
from mi_companion.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_current_parent,
)

__all__ = ["validate_pois_layer_node"]


def validate_pois_layer_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    for c in (check_current_parent,):
        reply = c(node, POINT_OF_INTERESTS_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted
