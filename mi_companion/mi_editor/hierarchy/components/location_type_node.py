from typing import Any, Optional

from mi_companion.layer_descriptors import LOCATION_TYPE_DESCRIPTOR
from mi_companion.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_current_parent,
    check_siblings_for_duplicates,
)

__all__ = ["validate_location_type_layer_node"]


def validate_location_type_layer_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    for c in (check_current_parent, check_siblings_for_duplicates):
        reply = c(node, LOCATION_TYPE_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted
