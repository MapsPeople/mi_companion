#!/usr/bin/python
import logging

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject, QgsSettings, QgsVectorLayer

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = []


def run(*, state: str = "Off") -> None:
    """
    Toggle all labels to state

    Either
    On
    or
    Off

    :param state:
    :return:
    """
    layers = list(QgsProject.instance().mapLayers().values())

    if isinstance(state, str):
        if state.lower().strip() == "off":
            state = False

    if not isinstance(state, bool):
        state = bool(state)

    if len(layers) == 0:
        logger.error("No layers found")

    for layer in layers:
        if isinstance(layer, QgsVectorLayer):
            if False:
                logger.warning(f"Toggle labels for {layer.name()} layer to {state}")
            layer.setLabelsEnabled(state)
            layer.triggerRepaint()
        else:
            logger.error(f"Did not toggle {layer.name()} label state to {state}")
