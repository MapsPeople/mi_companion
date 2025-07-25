#!/usr/bin/python
import logging
from typing import Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QWidget,
)

# noinspection PyUnresolvedReferences
from qgis.core import (
    Qgis,
    Qgis,
    QgsCategorizedSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsGeometryGeneratorSymbolLayer,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsProject,
    QgsRelation,
    QgsRendererCategory,
    QgsRendererCategory,
    QgsRuleBasedRenderer,
    QgsRuleBasedRenderer,
    QgsWkbTypes,
)

# noinspection PyUnresolvedReferences
from qgis.utils import iface

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]


def run(*, solution_id: str, new_solution_external_id: Optional[str] = None) -> None:
    """

    :param solution_id:
    :param new_solution_external_id:
    :return:
    """

    root_group = iface.layerTreeView().layerTreeModel().rootGroup()

    QtWidgets.QMessageBox.information(
        None,
        "Assigned external ID",
        f"Solution {solution_id} now has an external ID of {new_solution_external_id}",
    )


def fix_layer_references(layers):
    """
    Fix layer references and add anchor and rotation/scale geometry generators.

    Args:
        layers: List of vector layers to process
    """
    if not layers:
        logger.error(f"{layers=} was not found")
        return

    # Find location_type layer of solution
    location_type_layer = None
    location_layers = []

    for layer in layers:
        if not layer:
            continue

        layer_name = layer.name().lower()
        if "location_type" in layer_name:
            location_type_layer = layer
            logger.info(f"Found location_type layer: {layer.name()}")
        elif "location" in layer_name:
            location_layers.append(layer)
            logger.info(f"Found location layer: {layer.name()}")

    if not location_type_layer:
        logger.error("Location type layer not found")
        return

    if not location_layers:
        logger.warning("No location layers found")

    # Update references in location layers to point to the location_type layer
    for location_layer in location_layers:
        update_location_type_reference(location_layer, location_type_layer)

    logger.info(f"Fixed layer references for {len(location_layers)} location layers")


def update_location_type_reference(location_layer, location_type_layer):
    """Update the location_type reference in a location layer"""
    try:
        # Get field with location_type reference
        fields = location_layer.fields()
        location_type_field = None

        for field in fields:
            if "location_type" in field.name().lower():
                location_type_field = field.name()
                break

        if not location_type_field:
            logger.warning(f"No location_type field found in {location_layer.name()}")
            return

        # Create relation if needed
        relations = QgsProject.instance().relationManager().relations()
        relation_exists = False

        for rel_id, relation in relations.items():
            if (
                relation.referencingLayer() == location_layer
                and relation.referencedLayer() == location_type_layer
            ):
                relation_exists = True
                break

        if not relation_exists:
            # Create new relation
            relation = QgsRelation()
            relation.setId(f"{location_layer.id()}_{location_type_layer.id()}_relation")
            relation.setName(f"{location_layer.name()} to {location_type_layer.name()}")
            relation.setReferencedLayer(location_type_layer.id())
            relation.setReferencingLayer(location_layer.id())
            relation.addFieldPair(
                location_type_field, "id"
            )  # Assuming 'id' is the primary key

            # Add to project relations
            QgsProject.instance().relationManager().addRelation(relation)
            logger.info(
                f"Created relation between {location_layer.name()} and {location_type_layer.name()}"
            )

    except Exception as e:
        logger.error(f"Error updating location type reference: {str(e)}")


if __name__ == "__main__":

    def asijdauh():
        kemper_qgis = "4b2592bdd05342f2ada9cca3"

        run(solution_id=kemper_qgis)

    asijdauh()
