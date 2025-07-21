#!/usr/bin/python
import logging

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

# noinspection PyUnresolvedReferences
from qgis.utils import iface

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]


def run() -> None:
    """

    Assigns a coordinate value to all vertices in selected features of any geometry type

    :param value: Value to assign
    :param dimension: Which dimension to assign the value to
    :param only_active_layer: Only apply to active layer
    :return:
    """

    from jord.qlive_utilities import add_no_geom_layer

    columns = [{"a": "b", "c": "d"}, {"a": "c", "c": "d"}, {"a": "c", "c": "e"}]

    add_no_geom_layer(None, columns=columns)
