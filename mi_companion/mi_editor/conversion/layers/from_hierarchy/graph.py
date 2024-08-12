import logging

from integration_system.model import Solution

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.route_elements import (
    add_doors,
)

__all__ = ["add_venue_graph"]

logger = logging.getLogger(__name__)
# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant


def add_venue_graph(*, solution: Solution) -> None:
    location_group_items = None
    graph_key = None
    floor_index = None

    if (
        isinstance(location_group_items, QgsLayerTreeLayer)
        and "doors" in location_group_items.name()
        and graph_key is not None
        and read_bool_setting("ADD_DOORS")
    ):
        add_doors(
            floor_index=floor_index,
            graph_key=graph_key,
            location_group_items=location_group_items,
            solution=solution,
        )
    else:
        logger.debug(f"Skipped adding doors")
