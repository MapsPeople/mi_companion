import logging
import uuid
from typing import Any, Tuple

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsFeatureRequest,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsProject,
)

from mi_companion.configuration.options import read_bool_setting

logger = logging.getLogger(__name__)

__all__ = ["special_extract_layer_data", "extract_layer_data"]


def special_extract_layer_data(layer_tree_layer: Any) -> Tuple:  # TODO: REWRITE
    layer_attributes, layer_feature = extract_layer_data(layer_tree_layer)

    admin_id = layer_attributes["admin_id"] if "admin_id" in layer_attributes else None
    if admin_id is None:
        if read_bool_setting("GENERATE_MISSING_EXTERNAL_IDS"):
            admin_id = uuid.uuid4().hex
        else:
            raise ValueError(f"{layer_feature} is missing a valid admin id")

    external_id = (
        layer_attributes["external_id"] if "external_id" in layer_attributes else None
    )
    if external_id is None:
        if read_bool_setting("GENERATE_MISSING_EXTERNAL_IDS"):
            external_id = uuid.uuid4().hex
        else:
            raise ValueError(f"{layer_feature} is missing a valid external id")

    name = layer_attributes["name"] if "name" in layer_attributes else None

    if isinstance(name, QVariant):
        name = name.value()

    if name is None:
        name = external_id

    for k in layer_attributes.keys():
        if (
            isinstance(layer_attributes[k], str)
            and layer_attributes[k].lower().strip() == "none"
        ):
            layer_attributes[k] = None

    return admin_id, external_id, layer_attributes, layer_feature, name


def extract_layer_data(layer_tree_layer):
    geometry_layer = layer_tree_layer.layer()
    layer_feature = next(iter(geometry_layer.getFeatures()))
    layer_attributes = {
        k.name(): v
        for k, v in zip(
            layer_feature.fields(),
            layer_feature.attributes(),
        )
    }
    if len(layer_attributes) == 0:
        logger.error(
            f"Did not find attributes, skipping {layer_tree_layer.name()} {list(geometry_layer.getFeatures())}"
        )
    else:
        logger.info(f"found {layer_attributes=} for {layer_tree_layer.name()=}")
    return layer_attributes, layer_feature
