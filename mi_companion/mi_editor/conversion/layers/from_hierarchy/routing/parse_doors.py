import logging
from typing import Any, List, Mapping, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

from integration_system.tools.common_models import MIDoorType
from integration_system.model import Solution
from jord.qgis_utilities import GeometryIsEmptyError, feature_to_shapely
from mi_companion import DEFAULT_FIELDS, VERBOSE
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.common_attributes import (
    extract_single_level_str_map,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.extraction import (
    extract_feature_attributes,
)
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)


def add_doors(
    *,
    graph_key: str,
    door_layer_tree_node: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param graph_key:
    :param door_layer_tree_node:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    doors_linestring_layer = door_layer_tree_node.layer()
    for door_feature in doors_linestring_layer.getFeatures():
        door_attributes = extract_feature_attributes(door_feature)

        try:
            door_linestring = feature_to_shapely(door_feature)
        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e

        if door_linestring is None:
            logger.error(f"{door_linestring=}")

        fields = None
        if door_attributes is not None:
            fields_ = extract_single_level_str_map(
                door_attributes, nested_str_map_field_name="fields"
            )
            if fields_ is not None:
                fields = dict(fields_)

        door_key = solution.add_door(
            door_attributes["admin_id"],
            linestring=prepare_geom_for_mi_db(door_linestring, clean=False),
            door_type=get_door_type(door_attributes),
            floor_index=int(door_attributes["floor_index"]),
            graph_key=graph_key,
            fields=fields if fields is not None else DEFAULT_FIELDS,
        )
        if VERBOSE:
            logger.info("added door", door_key)


def get_door_type(door_attributes: Mapping[str, Any]) -> MIDoorType:
    """

    :param door_attributes:
    :return:
    """
    door_type = door_attributes["door_type"]

    if isinstance(door_type, str):
        ...
    elif isinstance(door_type, QVariant):
        # logger.warning(f"{typeToDisplayString(type(v))}")
        if door_type.isNull():  # isNull(v):
            door_type = None
        else:
            door_type = door_type.value()

    return MIDoorType(int(door_type))
