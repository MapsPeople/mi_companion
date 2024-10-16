import logging
import uuid
from typing import Any, Optional, Tuple

import shapely

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

__all__ = [
    "special_extract_layer_data",
    "extract_layer_data_single",
    "feature_to_shapely",
    "layer_data_generator",
    "MissingFeatureError",
]


def special_extract_layer_data(
    layer_tree_layer: Any, require_external_id: bool = False
) -> Tuple:  # TODO: REWRITE
    layer_attributes, layer_feature = extract_layer_data_single(layer_tree_layer)

    admin_id = layer_attributes["admin_id"] if "admin_id" in layer_attributes else None
    if admin_id is None:
        if read_bool_setting("GENERATE_MISSING_ADMIN_IDS"):
            admin_id = uuid.uuid4().hex
        else:
            raise ValueError(f"{layer_feature} is missing a valid admin id")
    elif isinstance(admin_id, QVariant):
        if admin_id.isNull():
            raise ValueError(f"{layer_feature} is missing a valid admin id")
        else:
            admin_id = str(admin_id.value())

    external_id = (
        layer_attributes["external_id"] if "external_id" in layer_attributes else None
    )
    if external_id is None:
        if read_bool_setting("GENERATE_MISSING_EXTERNAL_IDS"):
            external_id = uuid.uuid4().hex
        else:
            if require_external_id:
                raise ValueError(f"{layer_feature} is missing a valid external id")
    elif isinstance(external_id, QVariant):
        if external_id.isNull():
            external_id = None
        else:
            external_id = str(external_id.value())

    name = layer_attributes["name"] if "name" in layer_attributes else None

    if isinstance(name, QVariant):
        if external_id.isNull():
            name = None
        else:
            name = str(name.value())

    if name is None:
        name = external_id

    if name is None:
        raise ValueError(f"{layer_feature} is missing a valid name")

    for k in layer_attributes.keys():
        if (
            isinstance(layer_attributes[k], str)
            and layer_attributes[k].lower().strip() == "none"
        ):
            layer_attributes[k] = None
        elif isinstance(layer_attributes[k], QVariant):
            if layer_attributes[k].isNull():
                layer_attributes[k] = None
            else:
                layer_attributes[k] = str(layer_attributes[k].value())

    return admin_id, external_id, layer_attributes, layer_feature, name


def extract_layer_data_single(layer_tree_layer: Any) -> Tuple:
    geometry_layer = layer_tree_layer.layer()
    if (
        geometry_layer
        and geometry_layer.hasFeatures()
        and geometry_layer.featureCount() > 0
    ):
        if geometry_layer.featureCount() > 1:
            raise ValueError(f"{layer_tree_layer.name()} has more than one feature")

        for layer_feature in geometry_layer.getFeatures():
            layer_feature_attributes = {
                k.name(): v
                for k, v in zip(
                    layer_feature.fields(),
                    layer_feature.attributes(),
                )
            }
            if len(layer_feature_attributes) == 0:
                logger.error(
                    f"Did not find attributes, skipping {layer_tree_layer.name()} {list(geometry_layer.getFeatures())}"
                )
            else:
                logger.info(
                    f"found {layer_feature_attributes=} for {layer_tree_layer.name()=}"
                )
            return layer_feature_attributes, layer_feature

    raise MissingFeatureError(f"no feature was not found for {layer_tree_layer.name()}")


class MissingFeatureError(Exception):
    pass


def layer_data_generator(layer_tree_layer: Any) -> Tuple:
    geometry_layer = layer_tree_layer.layer()
    if (
        geometry_layer
        and geometry_layer.hasFeatures()
        and geometry_layer.featureCount() > 0
    ):
        for layer_feature in geometry_layer.getFeatures():
            layer_feature_attributes = {
                k.name(): v
                for k, v in zip(
                    layer_feature.fields(),
                    layer_feature.attributes(),
                )
            }
            if len(layer_feature_attributes) == 0:
                logger.error(
                    f"Did not find attributes, skipping {layer_tree_layer.name()} {list(geometry_layer.getFeatures())}"
                )
            else:
                logger.info(
                    f"found {layer_feature_attributes=} for {layer_tree_layer.name()=}"
                )
            yield layer_feature_attributes, layer_feature
    else:
        raise MissingFeatureError(
            f"no feature was not found for {layer_tree_layer.name()}"
        )


def feature_to_shapely(
    layer_feature: Any,
) -> Optional[shapely.geometry.base.BaseGeometry]:
    feature_geom = layer_feature.geometry()
    if feature_geom is not None:
        geom_wkb = feature_geom.asWkb()
        if geom_wkb is not None:
            if not isinstance(geom_wkb, bytes):
                geom_wkb = bytes(geom_wkb)
            return shapely.from_wkb(geom_wkb)
