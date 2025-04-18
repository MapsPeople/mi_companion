import logging
from enum import Enum
from typing import Any, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QMessageBox

# noinspection PyUnresolvedReferences
from qgis.core import Qgis, QgsProject

from .hierarchy_model import INVERSE_NODE_PARENT_MAPPING, NODE_PARENT_MAPPING
from .validation_dialog_utilities import (
    make_hierarchy_validation_dialog,
    make_temporary_toast,
)

__all__ = [
    "find_top_ancestor",
    "check_current_parent",
    "check_children",
    "check_siblings_for_duplicates",
    "ValidationResultEnum",
    "transfer_node_ownership",
]

ENABLE_UNDO = False

logger = logging.getLogger(__name__)


class ValidationResultEnum(Enum):
    accepted = "accepted"
    failure = "failure"
    rejected = "rejected"


def find_top_ancestor(node: Any) -> Any:
    """
    Recursively find the topmost ancestor of a node that isn't the layer tree root.



    :param node:  QgsLayerTreeNode to find ancestor for
    :return:       QgsLayerTreeNode: Topmost ancestor node before root, or original node if no valid ancestor
    found
    """
    if node is None:
        return None

    parent = node.parent()

    if (
        parent is None or parent == QgsProject.instance().layerTreeRoot()
    ):  # Hit root node
        return node

    return find_top_ancestor(parent) or node


def check_current_parent(
    node: Any, descriptor: str, parent: Optional[str] = None
) -> ValidationResultEnum:
    node_name = node.name()
    current_parent = node.parent()
    current_parent_name = str(current_parent.name())

    if descriptor not in NODE_PARENT_MAPPING:
        raise Exception(f"{descriptor} not in {NODE_PARENT_MAPPING}, contact Heider!")
        return ValidationResultEnum.failure

    if NODE_PARENT_MAPPING[descriptor] not in current_parent_name:
        reply = make_hierarchy_validation_dialog(
            "Invalid Layer Placement",
            f"You cannot move this {descriptor} element ({node_name}) into the group {current_parent_name}.\n"
            f"It must exist within a {NODE_PARENT_MAPPING[descriptor]} group.",
            add_reject_option=ENABLE_UNDO,
        )

        if reply == QMessageBox.RejectRole:
            return ValidationResultEnum.rejected

    return ValidationResultEnum.accepted


def check_children(
    node: Any, descriptor: str, parent: Optional[str] = None
) -> ValidationResultEnum:
    node_name = node.name()
    children = node.children()

    if descriptor not in INVERSE_NODE_PARENT_MAPPING:
        raise Exception(
            f"{descriptor} not in {INVERSE_NODE_PARENT_MAPPING}, " f"contact Heider!"
        )
        return ValidationResultEnum.failure

    for child in children:
        child_name = child.name()
        matched = False

        for child_descriptor in INVERSE_NODE_PARENT_MAPPING[descriptor]:
            if child_descriptor in child_name:
                matched = True

        if not matched:
            child_descriptor = None
            for descriptor in NODE_PARENT_MAPPING:
                if descriptor in child_name:
                    child_descriptor = descriptor
                    break

            reply = make_hierarchy_validation_dialog(
                "Invalid Layer Placement",
                f"This {child_descriptor} element ({child_name}) cannot exist within the group {node_name}.\n"
                f"It must within a {NODE_PARENT_MAPPING[child_descriptor]} group.",
                add_reject_option=ENABLE_UNDO,
            )

            if reply == QMessageBox.RejectRole:
                return ValidationResultEnum.rejected

    return ValidationResultEnum.accepted


def check_siblings_for_duplicates(
    node: Any, descriptor: str, parent: Optional[str] = None
) -> ValidationResultEnum:
    node_name = node.name()
    current_parent = node.parent()
    siblings = current_parent.children()

    found_duplicates = False
    for sibling in siblings:
        sibling_name = sibling.name()
        if (
            sibling_name == node_name
        ):  # SELF check TODO: MAYBE REFACTOR TO BE A LAYER POINTER
            continue
        else:
            if False:
                logger.error(f"node {node_name} has sibling {sibling_name}")

        if descriptor in sibling_name:
            found_duplicates = True

    if found_duplicates:
        reply = make_hierarchy_validation_dialog(
            "Duplicate Layer Type Detected",
            f"This group {current_parent.name()} can contain only one instance of this element type "
            f"{descriptor}.\n"
            f"Please remove the duplicate {descriptor} elements or move them to another compatible "
            f"{NODE_PARENT_MAPPING[descriptor]} group.",
        )

        if reply == QMessageBox.RejectRole:
            return ValidationResultEnum.rejected

    return ValidationResultEnum.accepted


def transfer_node_ownership(
    node: Any, to_group: Any  # QgsLayerTreeNode  # QgsLayerTreeGroup
) -> None:
    current_parent = node.parent()

    message = (
        f"Transferring {node.name()} to {to_group.name()} from {current_parent.name()}"
    )
    make_temporary_toast(message)

    if False:
        if True:
            to_group.insertChildNode(0, node.clone())
        else:
            to_group.insertLayer(0, node.layer())

        current_parent.removeChildNode(node)

        # gc_layers() # TOO EARLY, CAUSE A CRASH
    else:
        make_temporary_toast("Undo functionality disabled for now", level=Qgis.Critical)
