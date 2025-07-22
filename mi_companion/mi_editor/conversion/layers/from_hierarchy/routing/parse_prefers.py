import logging
from typing import Any, List, Optional

from sync_module.model import Solution
from jord.qgis_utilities import (
    GeometryIsEmptyError,
    extract_feature_attributes,
    feature_to_shapely,
)
from mi_companion import VERBOSE
from mi_companion.configuration import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.common_attributes import (
    extract_single_level_str_map,
)
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis

logger = logging.getLogger(__name__)


def add_prefers(
    graph_key: str,
    prefer_layer_tree_node: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param graph_key:
    :param prefer_layer_tree_node:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    prefers_linestring_layer = prefer_layer_tree_node.layer()
    for prefer_feature in prefers_linestring_layer.getFeatures():
        prefer_attributes = extract_feature_attributes(prefer_feature)

        try:
            prefer_point = feature_to_shapely(prefer_feature)

            if prefer_point is None:
                logger.error(
                    f'Error while adding {prefer_attributes["admin_id"]} {prefer_point=}'
                )
                continue

            if prefer_attributes is not None:
                fields = dict(
                    extract_single_level_str_map(
                        prefer_attributes, nested_str_map_field_name="fields"
                    )
                )
            else:
                fields = None

            prefer_key = solution.add_prefer(
                prefer_attributes["admin_id"],
                point=prepare_geom_for_mi_db_qgis(prefer_point),
                floor_index=int(prefer_attributes["floor_index"]),
                graph_key=graph_key,
                fields=fields,
            )
            if VERBOSE:
                logger.info("added prefer", prefer_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e
