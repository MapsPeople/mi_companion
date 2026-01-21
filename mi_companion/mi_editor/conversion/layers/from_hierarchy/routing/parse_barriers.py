import logging
from typing import Any, List, Optional

from jord.qgis_utilities import (
    GeometryIsEmptyError,
    extract_feature_attributes,
    extract_field_value,
    feature_to_shapely,
)
from mi_companion import VERBOSE
from mi_companion.configuration import read_bool_setting
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis
from mi_companion.qgis_utilities.common_attributes import (
    extract_single_level_str_map,
)
from sync_module.model import Solution

_logger = logging.getLogger(__name__)


def add_barriers(
    graph_key: str,
    barrier_layer_tree_node: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param graph_key:
    :param barrier_layer_tree_node:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    barriers_linestring_layer = barrier_layer_tree_node.layer()
    for barrier_feature in barriers_linestring_layer.getFeatures():
        barrier_attributes = extract_feature_attributes(barrier_feature)
        try:
            barrier_linestring = feature_to_shapely(barrier_feature)

            if barrier_linestring is None:
                _logger.error(f"{barrier_linestring=}")
                continue

            fields = None
            if barrier_attributes is not None:
                fields_ = extract_single_level_str_map(
                    barrier_attributes, nested_str_map_field_name="fields"
                )

                if fields_ is not None:
                    fields = dict(fields_)

            opening_hours = None
            if "opening_hours" in barrier_attributes:  # TODO: CONVERT THIS
                opening_hours = extract_field_value(barrier_attributes, "opening_hours")
                barrier_attributes.pop("opening_hours")

            wait_time = None
            if "wait_time" in barrier_attributes:
                wait_time = extract_field_value(barrier_attributes, "wait_time")
                barrier_attributes.pop("wait_time")
                if wait_time:
                    wait_time = int(wait_time)

            bearing = None
            if "bearing" in barrier_attributes:
                bearing = extract_field_value(barrier_attributes, "bearing")
                barrier_attributes.pop("bearing")
                if bearing:
                    bearing = float(bearing)

            barrier_key = solution.add_barrier(
                barrier_attributes["admin_id"],
                point=prepare_geom_for_mi_db_qgis(barrier_linestring),
                floor_index=int(barrier_attributes["floor_index"]),
                graph_key=graph_key,
                fields=fields,
                bearing=bearing,
                wait_time=wait_time,
                opening_hours=opening_hours,
            )

            if VERBOSE:
                _logger.info("added barrier", barrier_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e
