import logging

from integration_system.model import Solution

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from mi_companion.mi_editor.conversion.layers.from_hierarchy.route_elements import (
    add_route_elements,
)

__all__ = ["add_venue_graph"]

logger = logging.getLogger(__name__)
# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant


def add_venue_graph(*, solution: Solution) -> None:
    location_group_items = None
    graph_key = None
    floor_index = None

    # TODO: ADD graph?

    add_route_elements(floor_index, graph_key, location_group_items, solution)
