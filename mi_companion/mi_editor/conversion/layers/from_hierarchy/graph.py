import logging
from typing import Any, Optional, Tuple

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import Solution
from mi_companion import GRAPH_DATA_DESCRIPTOR
from mi_companion.mi_editor.conversion.layers.from_hierarchy.extraction import (
    extract_layer_data_single,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.route_elements import (
    add_route_elements,
)

__all__ = ["add_venue_graph"]

logger = logging.getLogger(__name__)
# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant


def get_graph_data(graph_group: Any, solution: Solution) -> Tuple:
    for graph_level_item in graph_group.children():
        if (
            isinstance(
                graph_level_item,
                QgsLayerTreeLayer,
            )
            and GRAPH_DATA_DESCRIPTOR.lower().strip()
            in str(graph_level_item.name()).lower().strip()
        ):
            layer_attributes, *_ = extract_layer_data_single(graph_level_item)
            graph_id = (
                layer_attributes["graph_id"] if "graph_id" in layer_attributes else None
            )

            graph_key = solution.add_graph(
                graph_id=graph_id, osm_xml=""  # TODO: ADD graph for OSM or edge layer?
            )
            return (graph_key,)
    return (None,)


def add_venue_graph(*, solution: Solution, graph_group: Any) -> Optional[str]:
    (graph_key,) = get_graph_data(graph_group, solution)

    if graph_key:
        add_route_elements(graph_key, graph_group, solution)

    return graph_key
