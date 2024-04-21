import logging
import uuid

from jord.qgis_utilities import read_plugin_setting

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsProject,
    QgsFeatureRequest,
)

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets, uic

from mi_companion import PROJECT_NAME, DEFAULT_PLUGIN_SETTINGS

logger = logging.getLogger(__name__)


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

    external_id = layer_attributes["external_id"]
    if external_id is None:
        if read_plugin_setting(
            "GENERATE_MISSING_EXTERNAL_IDS",
            default_value=DEFAULT_PLUGIN_SETTINGS["GENERATE_MISSING_EXTERNAL_IDS"],
            project_name=PROJECT_NAME,
        ):
            external_id = uuid.uuid4().hex
        else:
            raise ValueError(f"{layer_feature} is missing a valid external id")

    name = layer_attributes["name"]

    if name is None:
        name = external_id

    return external_id, layer_attributes, layer_feature, name
