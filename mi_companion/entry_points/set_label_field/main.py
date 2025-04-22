#!/usr/bin/python
import logging

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject, QgsSettings, QgsVectorLayer

from jord.qgis_utilities import set_label_styling
from mi_companion import LAYER_LABEL_VISIBLE_MIN_RATIO, RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = []


def run(
    *,
    field: str = "represent_value(location_type) + ': ' + name + ' - ' + external_id",
    min_ratio: float = LAYER_LABEL_VISIBLE_MIN_RATIO,
) -> None:
    """
    Set label value field

    Common options:

    location_type

    represent_value(location_type)

    external_id

    name


    :param min_ratio:
    :param field:
    :return:
    """
    layers = list(QgsProject.instance().mapLayers().values())

    if len(layers) == 0:
        logger.error("No layers found")

    for layer in layers:
        if isinstance(layer, QgsVectorLayer):
            set_label_styling(layer, field_name=field, min_ratio=min_ratio)
            #      layer.setLabelsEnabled(field)
            layer.triggerRepaint()
        else:
            logger.error(f"Did not toggle {layer.name()} label state to {field}")
