#!/usr/bin/python
import logging

from jord.qlive_utilities import add_no_geom_layer

logger = logging.getLogger(__name__)

__all__ = []


def run() -> None:
    """

    Assigns a coordinate value to all vertices in selected features of any geometry type

    :param value: Value to assign
    :param dimension: Which dimension to assign the value to
    :param only_active_layer: Only apply to active layer
    :return:
    """
    from qgis.utils import iface
    from qgis.core import QgsProject

    columns = [{"a": "b", "c": "d"}, {"a": "c", "c": "d"}, {"a": "c", "c": "e"}]

    add_no_geom_layer(None, columns=columns)
