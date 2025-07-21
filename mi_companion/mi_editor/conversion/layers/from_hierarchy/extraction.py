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

from jord.qgis_utilities import extract_layer_data_single
from mi_companion.configuration import read_bool_setting

logger = logging.getLogger(__name__)

__all__ = [
    "special_extract_layer_data",
]


def special_extract_layer_data(
    layer_tree_layer: Any, require_external_id: bool = False
) -> Tuple:  # TODO: REWRITE
    """

    :param layer_tree_layer:
    :param require_external_id:
    :return:
    """
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
        ...
    elif isinstance(external_id, QVariant):
        if external_id.isNull():
            external_id = None
        else:
            external_id = str(external_id.value())

    return admin_id, external_id, layer_attributes, layer_feature
