import logging
from qgis.PyQt.QtCore import QVariant
from typing import Any, List, Mapping, Optional

from jord.qgis_utilities import (
    extract_feature_attributes,
    extract_field_value,
    feature_to_shapely,
)
from mi_companion import VERBOSE
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis
from mi_companion.qgis_utilities.common_attributes import (
    extract_single_level_str_map,
)
from sync_module.model import Solution
from sync_module.shared import MIEntryPointType

_logger = logging.getLogger(__name__)


def add_entry_points(
    graph_key: str,
    entry_point_layer_tree_node: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param graph_key:
    :param entry_point_layer_tree_node:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    entry_points_linestring_layer = entry_point_layer_tree_node.layer()
    for entry_point_feature in entry_points_linestring_layer.getFeatures():
        entry_point_attributes = extract_feature_attributes(entry_point_feature)

        try:
            entry_point_geom = feature_to_shapely(entry_point_feature)

            if entry_point_geom is None:
                _logger.error(
                    f'Error while adding {entry_point_attributes["admin_id"]} {entry_point_geom=}'
                )
                continue

            fields = None
            if entry_point_attributes is not None:
                fields_ = extract_single_level_str_map(
                    entry_point_attributes, nested_str_map_field_name="fields"
                )
                if fields_ is not None:
                    fields = dict(fields_)

            opening_hours = None
            if "opening_hours" in entry_point_attributes:  # TODO: CONVERT THIS
                opening_hours = extract_field_value(
                    entry_point_attributes, "opening_hours"
                )
                entry_point_attributes.pop("opening_hours")

            wait_time = None
            if "wait_time" in entry_point_attributes:
                wait_time = extract_field_value(entry_point_attributes, "wait_time")
                entry_point_attributes.pop("wait_time")
                if wait_time:
                    wait_time = int(wait_time)

            entry_point_key = solution.add_entry_point(
                entry_point_attributes["admin_id"],
                point=prepare_geom_for_mi_db_qgis(entry_point_geom),
                entry_point_type=get_entry_point_type(entry_point_attributes),
                floor_index=int(entry_point_attributes["floor_index"]),
                graph_key=graph_key,
                fields=fields,
                # opening_hours=opening_hours,
                wait_time=wait_time,
            )

            if VERBOSE:
                _logger.info("added entry_point", entry_point_key)
        except Exception as e:
            _invalid = f"Invalid entry point: {e}"
            _logger.error(_invalid)
            if collect_invalid:
                issues.append(_invalid)
                continue
            else:
                raise e


def get_entry_point_type(entry_point_attributes: Mapping[str, Any]) -> MIEntryPointType:
    """

    :param entry_point_attributes:
    :return:
    """
    try:
        entry_point_type = entry_point_attributes["entry_point_type"]
    except Exception as e:
        _logger.error(e)
        _logger.error(entry_point_attributes)
        _logger.error(f"Defaulting to EntryPointType.any")
        entry_point_type = MIEntryPointType.any.value
        # raise e

    if isinstance(entry_point_type, str):
        ...
    elif isinstance(entry_point_type, QVariant):
        # logger.warning(f"{typeToDisplayString(type(v))}")
        if entry_point_type.isNull():  # isNull(v):
            entry_point_type = None
        else:
            entry_point_type = entry_point_type.value()

    return MIEntryPointType(int(entry_point_type))
