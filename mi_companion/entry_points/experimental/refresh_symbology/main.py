#!/usr/bin/python
import logging
from qgis.utils import iface

from mi_companion import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]
FUNCTION_DESCRIPTION = """...
"""
__doc__ = FUNCTION_DESCRIPTION


def run() -> None:
    """
    Toggle all labels to state

    :param state:
    :return:
    """

    layers = list(iface.layerTreeView().selectedLayers())  # TODO: MAYBE use this?

    layer = layers[0]

    renderer = layer.renderer()
    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())

    if True:
        # countSymbolFeatures() returns nullptr (None in Python) if the count has already been done
        # so we check the return value and if None is returned, we call our getFeatureCount() method
        # because in this case, the symbolFeatureCountMapChanged signal won't be fired
        if not layer.countSymbolFeatures():
            ...

        _logger.error(renderer.classAttribute())

        keys = renderer.legendKeys()

        print(_logger.name)

        _logger.error(f"legend keys: {keys}")

        for k in keys:
            _logger.error(
                f"Legend key expression: {renderer.legendKeyToExpression(k, layer)}"
            )
            _logger.error(f"Feature count for legend key: {layer.featureCount(k)}")
