import logging
import operator
from collections import defaultdict
from typing import Any, List, Mapping, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

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
from sync_module.model import Connection, Connector, Solution
from sync_module.shared import MIConnectionType

logger = logging.getLogger(__name__)


def assemble_connections(
    connections: Mapping[str, List[Connection]],
    solution: Solution,
    graph_key: str,
    *,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
):
    """

    :param connections:
    :param solution:
    :param graph_key:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    for connection_id, connector_tuples in connections.items():
        inner_connector_tuples, connection_types = zip(*connector_tuples)

        connection_type_set = set(connection_types)
        assert (
            len(connection_type_set) == 1
        ), f"Connectors with {connection_id} has varying {connection_type_set}, this is not allowed"

        connection_type = next(iter(connection_type_set))

        connector_list = list(inner_connector_tuples)
        connector_list.sort(key=operator.itemgetter(1))
        connectors = []
        for geom, floor_index, external_id in connector_list:
            connector_attributes = None  # TODO: GET THESE!

            fields = None
            if connector_attributes is not None:
                fields_ = extract_single_level_str_map(
                    connector_attributes, nested_str_map_field_name="fields"
                )
                if fields_ is not None:
                    fields = dict(fields_)

            connectors.append(
                Connector(
                    admin_id=external_id,
                    floor_index=floor_index,
                    point=prepare_geom_for_mi_db_qgis(geom),
                    fields=fields,
                )
            )

        try:
            connector_key = solution.add_connection(
                int(connection_id),
                connectors=connectors,
                connection_type=connection_type,
                graph_key=graph_key,
            )

            if VERBOSE:
                logger.info("added connector", connector_key)

        except Exception as e:
            _invalid = f"Invalid connection: {e}"
            logger.error(_invalid)
            if collect_invalid:
                issues.append(_invalid)
                continue
            else:
                raise e


def get_connections(connections_layer_tree_node: Any) -> dict:  # TODO: FINISH!
    """

    :param connections_layer_tree_node:
    :return:
    """
    connectors_linestring_layer = connections_layer_tree_node.layer()
    connections = defaultdict(list)
    for connector_feature in connectors_linestring_layer.getFeatures():
        connector_attributes = extract_feature_attributes(connector_feature)

        connection_id = connector_attributes["connection_id"]
        connector_floor_index = connector_attributes["floor_index"]
        connector_external_id = connector_attributes["admin_id"]

        connection_type = get_connection_type(connector_attributes)

        try:
            connector_point = feature_to_shapely(connector_feature)
        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e

        if connector_point is not None:
            connections[connection_id].append(
                (
                    (
                        connector_point,
                        int(connector_floor_index),
                        connector_external_id,
                    ),
                    connection_type,
                )
            )
        else:
            logger.error(
                f"Error while adding {connector_external_id} {connector_point=}"
            )
    return connections


def get_connection_type(connector_attributes: Mapping[str, Any]) -> MIConnectionType:
    """

    :param connector_attributes:
    :return:
    """
    connection_type = connector_attributes["connection_type"]

    if isinstance(connection_type, str):
        ...
    elif isinstance(connection_type, QVariant):
        # logger.warning(f"{typeToDisplayString(type(v))}")
        if connection_type.isNull():  # isNull(v):
            connection_type = None
        else:
            connection_type = connection_type.value()

    return MIConnectionType(int(connection_type))
