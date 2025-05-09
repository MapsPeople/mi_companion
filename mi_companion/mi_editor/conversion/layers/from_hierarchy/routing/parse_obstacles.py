import logging
from typing import Any, List, Optional

from integration_system.model import Solution
from jord.qgis_utilities import GeometryIsEmptyError, feature_to_shapely
from mi_companion import VERBOSE
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.extraction import (
    extract_feature_attributes,
)
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)


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
                logger.error(
                    f'Error while adding {obstacle_attributes["admin_id"]} {obstacle_poly=}'
                )
                continue

            # ss_fields = extract_nested_str_map(, nested_str_map_field_name='fields')
            fields = None

            obstacle_key = solution.add_obstacle(
                obstacle_attributes["admin_id"],
                polygon=prepare_geom_for_mi_db(obstacle_poly),
                floor_index=int(obstacle_attributes["floor_index"]),
                graph_key=graph_key,
                fields=fields,
            )
            if VERBOSE:
                logger.info("added obstacle", obstacle_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e
