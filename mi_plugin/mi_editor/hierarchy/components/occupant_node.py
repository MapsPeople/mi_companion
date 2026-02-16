from typing import Any, Optional

from mi_plugin.layer_descriptors import OCCUPANTS_DESCRIPTOR
from mi_plugin.mi_editor.hierarchy.hierarchy_utilities import (
    ValidationResultEnum,
    check_current_parent,
    check_siblings_for_duplicates,
)

__all__ = ["validate_occupants_layer_node"]


def validate_occupants_layer_node(
    node: Any, parent: Optional[str] = None
) -> ValidationResultEnum:
    for c in (check_current_parent, check_siblings_for_duplicates):
        reply = c(node, OCCUPANTS_DESCRIPTOR, parent)
        if reply != ValidationResultEnum.accepted:
            return reply

    return ValidationResultEnum.accepted
