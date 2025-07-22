import logging
from typing import Any, List, Mapping, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

from sync_module.shared.model.common_models import MIEntryPointType
from sync_module.model import Solution
from jord.qgis_utilities import extract_feature_attributes, feature_to_shapely
from mi_companion import VERBOSE
from mi_companion.mi_editor.conversion.layers.from_hierarchy.common_attributes import (
    extract_single_level_str_map,
)
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis

logger = logging.getLogger(__name__)


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
                logger.error(
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

            entry_point_key = solution.add_entry_point(
                entry_point_attributes["admin_id"],
                point=prepare_geom_for_mi_db_qgis(entry_point_geom),
                entry_point_type=get_entry_point_type(entry_point_attributes),
                floor_index=int(entry_point_attributes["floor_index"]),
                graph_key=graph_key,
                fields=fields,
            )

            if VERBOSE:
                logger.info("added entry_point", entry_point_key)
        except Exception as e:
            _invalid = f"Invalid entry point: {e}"
            logger.error(_invalid)
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
        logger.error(e)
        logger.error(entry_point_attributes)
        logger.error(f"Defaulting to EntryPointType.any")
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
