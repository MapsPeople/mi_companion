import logging
from typing import Any, List, Optional

from jord.qgis_utilities.conversion.features import feature_to_shapely, parse_q_value
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.graph_utilities.from_3d_lines import lines_3d_to_osm_xml
from integration_system.model import FALLBACK_OSM_GRAPH, Solution
from mi_companion import (
    NAVIGATION_GRAPH_LINES_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)

__all__ = ["add_3d_graph_edges"]


def add_3d_graph_edges(
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

    lines = []

    for location_group_item in graph_group.children():
        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and NAVIGATION_GRAPH_LINES_DESCRIPTOR in location_group_item.name()
        ):
            layer = location_group_item.layer()

            if layer:
                for ith, layer_feature in enumerate(layer.getFeatures()):
                    feature_attributes = {
                        k.name(): parse_q_value(v)
                        for k, v in zip(
                            layer_feature.fields(),
                            layer_feature.attributes(),
                        )
                    }

                    feature_attributes["osmid"] = str(-ith)

                    graph_line = prepare_geom_for_mi_db(
                        feature_to_shapely(layer_feature), clean=False
                    )

                    lines.append((graph_line, feature_attributes))

    try:
        osm_xml = lines_3d_to_osm_xml(lines).decode(
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
