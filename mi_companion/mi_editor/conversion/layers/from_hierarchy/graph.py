import logging
from typing import Any, List, Optional, Tuple

from jord.qgis_utilities.conversion.features import feature_to_shapely, parse_q_value

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.graph_utilities import lines_to_osm_xml
from integration_system.model import FALLBACK_OSM_GRAPH, Solution
from mi_companion import GRAPH_DATA_DESCRIPTOR, NAVIGATION_HORIZONTAL_LINES_DESCRIPTOR
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.extraction import (
    extract_layer_data_single,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.route_elements import (
    add_route_elements,
)
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db

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


def add_graph_edges(
    *,
    graph_key: str,
    graph_group: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    if not read_bool_setting("UPLOAD_OSM_GRAPH"):
        logger.warning("OSM graph upload is disabled")
        return

    verticals = {}
    horizontals = []

    for location_group_item in graph_group.children():
        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and NAVIGATION_HORIZONTAL_LINES_DESCRIPTOR in location_group_item.name()
        ):
            layer = location_group_item.layer()

            if layer:
                for layer_feature in layer.getFeatures():
                    feature_attributes = {
                        k.name(): parse_q_value(v)
                        for k, v in zip(
                            layer_feature.fields(),
                            layer_feature.attributes(),
                        )
                    }

                    location_geometry = prepare_geom_for_mi_db(
                        feature_to_shapely(layer_feature), clean=False
                    )

                    horizontals.append((location_geometry, feature_attributes))

    # verticals[] = ...

    try:
        osm_xml = lines_to_osm_xml(horizontals, verticals=verticals).decode(
            "utf-8"
        )  # OSMNX HAS SOME WEIRD BUGS!
    except Exception as e:
        logger.error(e)
        osm_xml = FALLBACK_OSM_GRAPH
        if True:
            raise e

    try:
        solution.update_graph(graph_key, osm_xml=osm_xml)
    except Exception as e:
        _invalid = f"Invalid graph: {e}"
        logger.error(_invalid)
        if collect_invalid:
            issues.append(_invalid)
        else:
            raise e


def add_venue_graph(
    *,
    solution: Solution,
    graph_group: Any,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> Optional[str]:
    (graph_key,) = get_graph_data(
        graph_group, solution
    )  # TODO: ADD graph_bounds from a poly layer

    if graph_key:
        add_graph_edges(
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
