import logging
from typing import Any, Tuple

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import Solution
from mi_companion.configuration.constants import GRAPH_DATA_DESCRIPTOR
from mi_companion.mi_editor.conversion.layers.from_hierarchy.extraction import (
    extract_layer_data,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.route_elements import (
    add_route_elements,
)

__all__ = ["add_venue_graph"]

logger = logging.getLogger(__name__)
# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant


def get_graph_data(floor_group_items: Any, solution: Solution) -> Tuple:
    for floor_level_item in floor_group_items.children():
        if (
            isinstance(
                floor_level_item,
                QgsLayerTreeLayer,
            )
            and GRAPH_DATA_DESCRIPTOR.lower().strip()
            in str(floor_level_item.name()).lower().strip()
        ):
            graph_id, *_ = extract_layer_data(floor_level_item)

            graph_key = solution.add_graph(
                graph_id=graph_id, osm_xml=""  # TODO: ADD graph for OSM or edge layer?
            )
            return (graph_key,)
    return (None,)


def add_venue_graph(*, solution: Solution, venue_group_item: Any) -> None:
    graph_key = get_graph_data(venue_group_item, solution)

    if graph_key:
        add_route_elements(graph_key, venue_group_item, solution)
