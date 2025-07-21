import logging

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject
from typing import Any, List, Optional, Tuple

from integration_system.model import FALLBACK_OSM_GRAPH, Solution
from jord.qgis_utilities import extract_layer_data_single, feature_to_shapely
from mi_companion import UPLOAD_ERROR_CONFIRMATION_TITLE
from mi_companion.layer_descriptors import GRAPH_BOUND_DESCRIPTOR
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis
from .graph_3d_network import add_3d_graph_edges
from .route_elements import (
    add_route_elements,
)

__all__ = ["add_venue_graph"]

logger = logging.getLogger(__name__)


def get_graph_data(graph_group: Any, solution: Solution) -> Tuple:
    """

    :param graph_group:
    :param solution:
    :return:
    """
    for graph_level_item in graph_group.children():
        if (
            isinstance(
                graph_level_item,
                QgsLayerTreeLayer,
            )
            and GRAPH_BOUND_DESCRIPTOR.lower().strip()
            in str(graph_level_item.name()).lower().strip()
        ):
            layer_attributes, layer_geom = extract_layer_data_single(graph_level_item)
            graph_id = (
                layer_attributes["graph_id"] if "graph_id" in layer_attributes else None
            )

            try:
                graph_polygon = feature_to_shapely(layer_geom)

            except Exception as e:
                _error = str(e)
                reply = QMessageBox.question(
                    None,
                    UPLOAD_ERROR_CONFIRMATION_TITLE,
                    _error,
                    QMessageBox.Ok,
                    QMessageBox.Cancel,
                )
                # if reply == QMessageBox.Cancel:
                raise Exception(_error)

            graph_bound_geom = prepare_geom_for_mi_db_qgis(graph_polygon, clean=True)

            graph_key = solution.add_graph(
                graph_id=graph_id,
                osm_xml=FALLBACK_OSM_GRAPH,
                boundary=graph_bound_geom,
            )
            return (graph_key,)

    return (None,)


def add_venue_graph(
    *,
    solution: Solution,
    graph_group: Any,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> Optional[str]:
    """

    :param solution:
    :param graph_group:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    (graph_key,) = get_graph_data(graph_group, solution)

    if graph_key is None:
        ...

    if graph_key:
        # add_graph_edges(
        add_3d_graph_edges(
            graph_key=graph_key,
            graph_group=graph_group,
            solution=solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )

    if graph_key:
        add_route_elements(
            graph_key,
            graph_group,
            solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )

    return graph_key
