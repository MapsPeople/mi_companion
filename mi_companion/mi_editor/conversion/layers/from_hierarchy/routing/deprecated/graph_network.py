import logging
from collections import defaultdict
from typing import Any, List, Optional

from jord.qgis_utilities.conversion.features import feature_to_shapely, parse_q_value
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.graph_utilities.deprecated.old_graph_format import (
    lines_and_points_to_osm_xml,
)
from integration_system.model import FALLBACK_OSM_GRAPH, Solution
from mi_companion import (
    NAVIGATION_HORIZONTAL_LINES_DESCRIPTOR,
    NAVIGATION_VERTICAL_LINES_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)
__all__ = ["add_graph_edges"]


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

        elif (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and NAVIGATION_VERTICAL_LINES_DESCRIPTOR in location_group_item.name()
        ):
            layer = location_group_item.layer()

            if layer:
                vert = defaultdict(list)
                for layer_feature in layer.getFeatures():
                    feature_attributes = {
                        k.name(): parse_q_value(v)
                        for k, v in zip(
                            layer_feature.fields(),
                            layer_feature.attributes(),
                        )
                    }

                    vert_id = feature_attributes.pop("vertical_id")
                    v_type = feature_attributes.pop("highway")
                    level = feature_attributes.pop("level")
                    location_geometry = prepare_geom_for_mi_db(
                        feature_to_shapely(layer_feature), clean=False
                    )

                    vert[vert_id].append(
                        (v_type, level, location_geometry, feature_attributes)
                    )

                for vert_id, vert_data in vert.items():
                    gen = iter(vert_data)
                    v_type, level, location_geometry, feature_attributes = next(gen)
                    levels = [level]

                    for _v_type, _level, location_geometry, feature_attributes in gen:
                        assert (
                            level not in levels
                        ), f"Duplicate level: {level} for vertical_line {vert_id}"
                        levels.append(_level)
                        assert (
                            v_type == _v_type
                        ), f"Type mismatch: {v_type} != {_v_type} for vertical_line {vert_id}"
                        assert feature_attributes == feature_attributes, (
                            f"Attribute mismatch: {feature_attributes} != "
                            f"{feature_attributes} for vertical_line "
                            f"{vert_id}"
                        )

                    level_geoms = {}
                    for v in vert_data:
                        _, level, location_geometry, _ = v
                        level_geoms[level] = location_geometry

                    verticals[vert_id] = (v_type, level_geoms, feature_attributes)

    try:
        osm_xml = lines_and_points_to_osm_xml(
            horizontals=horizontals, verticals=verticals
        ).decode(
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
