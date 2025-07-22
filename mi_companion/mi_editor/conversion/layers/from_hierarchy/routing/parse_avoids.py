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


def add_avoids(
    graph_key: str,
    avoid_layer_tree_node: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param graph_key:
    :param avoid_layer_tree_node:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    avoids_linestring_layer = avoid_layer_tree_node.layer()
    for avoid_feature in avoids_linestring_layer.getFeatures():
        avoid_attributes = extract_feature_attributes(avoid_feature)

        try:
            avoid_point = feature_to_shapely(avoid_feature)

            if avoid_point is None:
                logger.error(f"{avoid_point=}")
                logger.error(
                    f'Error while adding {avoid_attributes["admin_id"]} {avoid_point=}'
                )
                continue

            fields = None
            if avoid_attributes is not None:
                fields_ = extract_single_level_str_map(
                    avoid_attributes, nested_str_map_field_name="fields"
                )
                if fields_ is not None:
                    fields = dict(fields_)

            avoid_key = solution.add_avoid(
                avoid_attributes["admin_id"],
                point=prepare_geom_for_mi_db_qgis(avoid_point),
                floor_index=int(avoid_attributes["floor_index"]),
                graph_key=graph_key,
                fields=fields,
            )

            if VERBOSE:
                logger.info("added avoid", avoid_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e
