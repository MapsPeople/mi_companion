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
from mi_plugin.configuration.options import read_bool_setting
from mi_plugin.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis
from mi_plugin.qgis_utilities.common_attributes import (
    extract_single_level_str_map,
)

_logger = logging.getLogger(__name__)


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
                _logger.error(
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

            opening_hours = None
            if "opening_hours" in prefer_attributes:  # TODO: CONVERT THIS
                opening_hours = extract_field_value(prefer_attributes, "opening_hours")
                prefer_attributes.pop("opening_hours")

            prefer_key = solution.add_prefer(
                prefer_attributes["admin_id"],
                point=prepare_geom_for_mi_db_qgis(prefer_point),
                floor_index=int(prefer_attributes["floor_index"]),
                graph_key=graph_key,
                fields=fields,
                # opening_hours=opening_hours,
            )
            if VERBOSE:
                _logger.info("added prefer", prefer_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e
