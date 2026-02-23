import logging
from typing import Any, List, Optional

from qgis.core import (
    QgsLayerTreeLayer,
)

from jord.qgis_utilities import feature_to_shapely, parse_q_value
from jord.qgis_utilities.conversion.features import set_z_from_m
from mi_plugin.layer_descriptors import GRAPH_LINES_DESCRIPTOR
from mi_plugin.constants import USE_FUZZY_MATCHING_FOR_3D_GRAPH_NODES
from mi_plugin.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis
from sync_module.mi_sync_constants import GEOMETRY_DIFFERENCE_TOLERANCE_4326
from sync_module.model import FALLBACK_OSM_GRAPH, Solution
from sync_module.tools import lines_3d_to_osm_xml
from sync_module.tools.graph_utilities.experimental.from_lines_fuzzy import (
    lines_3d_to_osm_xml_fuzzy,
)

_logger = logging.getLogger(__name__)

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
    """

    :param graph_key:
    :param graph_group:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    lines = []

    for location_group_item in graph_group.children():
        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and GRAPH_LINES_DESCRIPTOR in location_group_item.name()
        ):
            layer = location_group_item.layer()

            if layer:
                for ith, layer_feature in enumerate(layer.getFeatures(), start=1):
                    feature_attributes = {
                        k.name(): parse_q_value(v)
                        for k, v in zip(
                            layer_feature.fields(),
                            layer_feature.attributes(),
                        )
                    }

                    feature_attributes["osmid"] = str(-ith)

                    lines.append(
                        (
                            prepare_geom_for_mi_db_qgis(
                                feature_to_shapely(
                                    set_z_from_m(layer_feature, raise_on_missing=True),
                                    validate=False,
                                ),
                                clean=False,
                            ),
                            feature_attributes,
                        )
                    )

    try:
        if USE_FUZZY_MATCHING_FOR_3D_GRAPH_NODES:
            _logger.warning(
                "Using fuzzy matching for 3D graph nodes. This may lead to unexpected results. Use with caution."
            )
            osm_xml = lines_3d_to_osm_xml_fuzzy(
                lines, epsilon=GEOMETRY_DIFFERENCE_TOLERANCE_4326
            ).decode(
                "utf-8"
            )  # OSMNX HAS SOME WEIRD BUGS!
        else:
            osm_xml = lines_3d_to_osm_xml(lines).decode(
                "utf-8"
            )  # OSMNX HAS SOME WEIRD BUGS!
    except Exception as e:
        _logger.error(e)
        osm_xml = FALLBACK_OSM_GRAPH
        if True:
            raise e

    try:
        solution.update_graph(graph_key, osm_xml=osm_xml)
    except Exception as e:
        _invalid = f"Invalid graph: {e}"
        _logger.error(_invalid)
        if collect_invalid:
            issues.append(_invalid)
        else:
            raise e
