import logging

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QMessageBox

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsLayerTree,
    QgsLayerTreeModel,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)
from typing import Any, Optional

from jord.qgis_utilities import disconnect_signal, gc_layers, reconnect_signal
from mi_companion.layer_descriptors import (
    DATABASE_GROUP_DESCRIPTOR,
    ROUTE_ELEMENT_LAYER_DESCRIPTORS,
)
from .components import NODE_VALIDATION_MAPPING
from .hierarchy_utilities import (
    ValidationResultEnum,
    find_top_ancestor,
    transfer_node_ownership,
)
from .validation_dialog_utilities import (
    make_hierarchy_validation_dialog,
    make_temporary_toast,
)

logger = logging.getLogger(__name__)

__all__ = [
    "add_solution_hierarchy_change_listener",
    "remove_solution_hierarchy_change_listener",
]

PREVIOUS_PARENT = {}
PREVIOUS_NAME = {}

# NAMES_TO_BE_REMOVED_FROM = defaultdict(list)


def clear_mappings():
    PREVIOUS_NAME.clear()
    PREVIOUS_PARENT.clear()


def validate_hierarchy(node: Any, parent: Optional[str] = None) -> ValidationResultEnum:
    top_ancestor = find_top_ancestor(node)

    if top_ancestor is None:
        if False:
            logger.error(f"{node}: No valid ancestor")
        return ValidationResultEnum.failure

    top_ancestor_name = top_ancestor.name()

    if DATABASE_GROUP_DESCRIPTOR not in top_ancestor_name:
        if False:
            logger.error(f"{DATABASE_GROUP_DESCRIPTOR} not in {top_ancestor_name}")
        return ValidationResultEnum.failure

    node_name = str(node.name())

    parent_name = str(node.parent().name())
    for a in ROUTE_ELEMENT_LAYER_DESCRIPTORS:
        # IGNORED SUB LAYERS FOR NOW
        if a in parent_name:
            logger.warning(
                f"Hierarchy Validation for {node_name} was skipped, due to {a} was found in {parent_name=}, "
                f"for now these sub-hierarchies are not validated"
            )
            return ValidationResultEnum.failure

    matched_validator = None
    for descriptor, validator in NODE_VALIDATION_MAPPING.items():
        if descriptor in node_name:
            if matched_validator is None:
                matched_validator = validator
            else:
                reply = make_hierarchy_validation_dialog(
                    "Ambiguous Layer Name",
                    f"Multiple matches for descriptor {descriptor}: {node_name}, already found: "
                    f"{matched_validator.__name__}",
                )

                if reply == QMessageBox.RejectRole:
                    return ValidationResultEnum.rejected

    if matched_validator is not None:
        return matched_validator(node, parent)
    else:
        reply = make_hierarchy_validation_dialog(
            "Unknown Layer",
            f"This element ({node_name}) is not recognized as part of a valid MapsIndoors hierarchy. Unknown "
            f"layers will be excluded from the upload.",
        )

        if reply == QMessageBox.RejectRole:
            return ValidationResultEnum.rejected

    return ValidationResultEnum.accepted


def hierarchy_change(node, signal_provider=None) -> None:
    validate_hierarchy(node)


def name_changed(node, new_name) -> None:
    result = validate_hierarchy(node)

    if result == ValidationResultEnum.rejected:
        node.setName(PREVIOUS_NAME[node])
    else:
        PREVIOUS_NAME[node] = new_name


def will_add_children(node, index_from, index_to) -> None:
    new_children = node.children()
    # if len(new_children) == 0:
    #  return

    # new_children = new_children[index_from:index_to + 1]

    # for child in new_children:
    #  FOUND_PREV_CONTEXT[child.name()] = child.parent()


def removed_children(node, index_from, index_to) -> None:
    node_name = node.name()
    # for child_name in NAMES_TO_BE_REMOVED_FROM[node.name()]:
    #  if child_name in FOUND_PREV_CONTEXT:
    #    FOUND_PREV_CONTEXT.pop(child_name)

    # NAMES_TO_BE_REMOVED_FROM[node_name].clear()
    # NAMES_TO_BE_REMOVED_FROM.pop(node_name)


def will_remove_children(node, index_from, index_to) -> None:
    existing_children = node.children()
    if len(existing_children) == 0:
        return

    for child in existing_children[index_from : index_to + 1]:
        PREVIOUS_PARENT[child.name()] = node

    logger.error([f"{c}:{node.name()}" for c, node in PREVIOUS_PARENT.items()])
    # NAMES_TO_BE_REMOVED_FROM[node.name()] = [child.name() for child in existing_children]


def added_children(node, index_from, index_to) -> None:
    new_children = node.children()
    if len(new_children) == 0:
        return

    new_children = new_children[index_from : index_to + 1]

    if False:
        logger.error(f"{node.name()}, {index_from}, {index_to}, {new_children}")

    for child in new_children:
        child_name = child.name()
        previous_parent = None

        if child_name in PREVIOUS_PARENT:
            previous_parent = PREVIOUS_PARENT.pop(child_name)
            PREVIOUS_NAME[child] = child_name

        result = validate_hierarchy(child, previous_parent)

        if result == ValidationResultEnum.rejected:
            if previous_parent is not None:
                transfer_node_ownership(child, previous_parent)
            else:
                remove_node(child)
        else:
            PREVIOUS_PARENT[child_name] = node


def remove_node(child: Any) -> None:
    NODE_TO_BE_REMOVED.add(child)


NODE_TO_BE_REMOVED = set()


def add_solution_hierarchy_change_listener() -> None:
    layer_tree_root = (
        QgsProject.instance().layerTreeRoot()
    )  # TODO: MAYBE USE DATABASE ROOT

    reconnect_signal(layer_tree_root.nameChanged, name_changed, name_changed)
    reconnect_signal(layer_tree_root.addedChildren, added_children, added_children)

    # reconnect_signal(layer_tree_root.removedChildren, remove_children)

    # reconnect_signal(layer_tree_root.willAddChildren, will_add_children, will_add_children)

    # reconnect_signal(layer_tree_root.willRemoveChildren, will_remove_children, will_remove_children)
    # reconnect_signal(layer_tree_root.removedChildren, removed_children, removed_children)

    # layer_tree_root.customPropertyChanged
    #  layer_tree_root.expandedChanged
    #  layer_tree_root.visibilityChanged

    # QgsMapLayerRegistry.instance().layersWillBeRemoved
    # reconnect_signal(layer_tree_root.layerOrderChanged, liste)
    # reconnect_signal(layer_tree_root.customLayerOrderChanged, liste)


def remove_solution_hierarchy_change_listener() -> None:
    layer_tree_root = QgsProject.instance().layerTreeRoot()
    clear_mappings()

    disconnect_signal(layer_tree_root.nameChanged, name_changed)
    disconnect_signal(layer_tree_root.addedChildren, added_children)
    # disconnect_signal(layer_tree_root.removedChildren, remove_children)


# Define a function to handle the layer tree update signal
def remove_children() -> None:
    if False:
        for node in range(len(NODE_TO_BE_REMOVED)):
            node = NODE_TO_BE_REMOVED.pop()
            message = f"Trying to remove duplicate element {node.name()}."
            make_temporary_toast(message)

            pa = node.parent()
            pa.removeChildNode(
                node
            )  # CANNOT REMOVE IMMEDIATELY, some event are still rely on child
            # existence at this point...

            child_layer_id = None
            if hasattr(node, "layerId"):
                child_layer_id = node.layerId()

            if child_layer_id is not None:
                if False:
                    pa.removeLayer(node.layer())

                QgsProject.instance().removeMapLayer(child_layer_id)

    if False:
        gc_layers()
