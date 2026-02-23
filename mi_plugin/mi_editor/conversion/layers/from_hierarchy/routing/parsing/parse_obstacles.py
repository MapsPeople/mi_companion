import logging
from typing import Any, List, Optional

from sync_module.model import Solution

from jord.qgis_utilities import (
    extract_feature_attributes,
    extract_field_value,
    feature_to_shapely,
)
from jord.qgis_utilities.exceptions import GeometryIsEmptyError
from mi_plugin import VERBOSE
from mi_plugin.configuration import read_bool_setting
from mi_plugin.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis
from mi_plugin.qgis_utilities.common_attributes import (
    extract_single_level_str_map,
)

_logger = logging.getLogger(__name__)


def add_obstacles(
    graph_key: str,
    obstacle_layer_tree_node: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param graph_key:
    :param obstacle_layer_tree_node:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    obstacles_linestring_layer = obstacle_layer_tree_node.layer()
    for obstacle_feature in obstacles_linestring_layer.getFeatures():
        obstacle_attributes = extract_feature_attributes(obstacle_feature)
        try:
            obstacle_poly = feature_to_shapely(obstacle_feature)

            if obstacle_poly is None:
                _logger.error(
                    f'Error while adding {obstacle_attributes["admin_id"]} {obstacle_poly=}'
                )
                continue

            fields = None

            if obstacle_attributes is not None:
                fields_ = extract_single_level_str_map(
                    obstacle_attributes, nested_str_map_field_name="fields"
                )
                if fields_ is not None:
                    fields = dict(fields_)

            opening_hours = None
            if "opening_hours" in obstacle_attributes:  # TODO: CONVERT THIS
                opening_hours = extract_field_value(
                    obstacle_attributes, "opening_hours"
                )
                obstacle_attributes.pop("opening_hours")

            obstacle_key = solution.add_obstacle(
                obstacle_attributes["admin_id"],
                polygon=prepare_geom_for_mi_db_qgis(obstacle_poly),
                floor_index=int(obstacle_attributes["floor_index"]),
                graph_key=graph_key,
                fields=fields,
                # opening_hours=opening_hours,
            )
            if VERBOSE:
                _logger.info("added obstacle", obstacle_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e
