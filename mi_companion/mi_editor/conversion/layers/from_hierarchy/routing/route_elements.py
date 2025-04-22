import logging
import operator
from collections import defaultdict
from typing import Any, List, Mapping, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import (
    Connection,
    Connector,
    Solution,
)
from jord.qgis_utilities.conversion.features import (
    GeometryIsEmptyError,
    feature_to_shapely,
)
from mi_companion import (
    MAKE_FLOOR_WISE_LAYERS,
    VERBOSE,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.layer_descriptors import (
    AVOIDS_GROUP_DESCRIPTOR,
    BARRIERS_GROUP_DESCRIPTOR,
    CONNECTORS_GROUP_DESCRIPTOR,
    DOORS_GROUP_DESCRIPTOR,
    ENTRY_POINTS_GROUP_DESCRIPTOR,
    OBSTACLES_GROUP_DESCRIPTOR,
    PREFERS_GROUP_DESCRIPTOR,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.extraction import (
    extract_feature_attributes,
)
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db
from .parsing import (
    get_connection_type,
    get_door_type,
    get_entry_point_type,
)

logger = logging.getLogger(__name__)

__all__ = [
    "add_doors",
    "add_barriers",
    "add_avoids",
    "add_obstacles",
    "add_prefers",
    "get_connections",
    "add_entry_points",
    "add_route_elements",
]


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

        door_key = solution.add_door(
            door_attributes["admin_id"],
            linestring=prepare_geom_for_mi_db(door_linestring, clean=False),
            door_type=get_door_type(door_attributes),
            floor_index=int(door_attributes["floor_index"]),
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added door", door_key)


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
                logger.error(f"{barrier_linestring=}")
                continue

            barrier_key = solution.add_barrier(
                barrier_attributes["admin_id"],
                point=prepare_geom_for_mi_db(barrier_linestring),
                floor_index=int(barrier_attributes["floor_index"]),
                graph_key=graph_key,
            )

            if VERBOSE:
                logger.info("added barrier", barrier_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e


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

            avoid_key = solution.add_avoid(
                avoid_attributes["admin_id"],
                point=prepare_geom_for_mi_db(avoid_point),
                floor_index=int(avoid_attributes["floor_index"]),
                graph_key=graph_key,
            )

            if VERBOSE:
                logger.info("added avoid", avoid_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e


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

            prefer_key = solution.add_prefer(
                prefer_attributes["admin_id"],
                point=prepare_geom_for_mi_db(prefer_point),
                floor_index=int(prefer_attributes["floor_index"]),
                graph_key=graph_key,
            )
            if VERBOSE:
                logger.info("added prefer", prefer_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e


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

            obstacle_key = solution.add_obstacle(
                obstacle_attributes["admin_id"],
                polygon=prepare_geom_for_mi_db(obstacle_poly),
                floor_index=int(obstacle_attributes["floor_index"]),
                graph_key=graph_key,
            )
            if VERBOSE:
                logger.info("added obstacle", obstacle_key)

        except GeometryIsEmptyError as e:
            if not read_bool_setting("IGNORE_EMPTY_SHAPES"):
                raise e


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

            entry_point_key = solution.add_entry_point(
                entry_point_attributes["admin_id"],
                point=prepare_geom_for_mi_db(entry_point_geom),
                entry_point_type=get_entry_point_type(entry_point_attributes),
                floor_index=int(entry_point_attributes["floor_index"]),
                graph_key=graph_key,
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


def recurse_layers(group):
    for layer in group.children():
        if isinstance(layer, QgsLayerTreeGroup):
            yield from recurse_layers(layer)
        elif isinstance(layer, QgsLayerTreeLayer):
            yield layer


def add_route_elements(
    graph_key: str,
    graph_group: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param graph_key:
    :param graph_group:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """

    if read_bool_setting("ADD_ROUTE_ELEMENTS") and graph_key is not None:
        for ith_graph_group_item, graph_group_item in enumerate(graph_group.children()):
            if MAKE_FLOOR_WISE_LAYERS:
                add_route_element_groups(
                    collect_errors,
                    collect_invalid,
                    collect_warnings,
                    graph_group_item,
                    graph_key,
                    issues,
                    solution,
                )
            else:
                add_flat_route_element_layers(
                    collect_errors,
                    collect_invalid,
                    collect_warnings,
                    graph_group_item,
                    graph_key,
                    issues,
                    solution,
                )


def add_route_element_groups(
    collect_errors,
    collect_invalid,
    collect_warnings,
    graph_group_item,
    graph_key,
    issues,
    solution,
):
    if (
        isinstance(graph_group_item, QgsLayerTreeGroup)
        and DOORS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        for sub_graph_group_item in recurse_layers(graph_group_item):
            add_doors(
                graph_key=graph_key,
                door_layer_tree_node=sub_graph_group_item,
                solution=solution,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )
    else:
        logger.debug(f"Skipped adding {DOORS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeGroup)
        and BARRIERS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        for sub_graph_group_item in recurse_layers(graph_group_item):
            add_barriers(
                graph_key=graph_key,
                barrier_layer_tree_node=sub_graph_group_item,
                solution=solution,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )
    else:
        logger.debug(f"Skipped adding {BARRIERS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeGroup)
        and AVOIDS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        for sub_graph_group_item in recurse_layers(graph_group_item):
            add_avoids(
                graph_key=graph_key,
                avoid_layer_tree_node=sub_graph_group_item,
                solution=solution,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )
    else:
        logger.debug(f"Skipped adding {AVOIDS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeGroup)
        and PREFERS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        for sub_graph_group_item in recurse_layers(graph_group_item):
            add_prefers(
                graph_key=graph_key,
                prefer_layer_tree_node=sub_graph_group_item,
                solution=solution,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )
    else:
        logger.debug(f"Skipped adding {PREFERS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeGroup)
        and OBSTACLES_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        for sub_graph_group_item in recurse_layers(graph_group_item):
            add_obstacles(
                graph_key=graph_key,
                obstacle_layer_tree_node=sub_graph_group_item,
                solution=solution,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )
    else:
        logger.debug(f"Skipped adding {OBSTACLES_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeGroup)
        and ENTRY_POINTS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        for sub_graph_group_item in recurse_layers(graph_group_item):
            add_entry_points(
                graph_key=graph_key,
                entry_point_layer_tree_node=sub_graph_group_item,
                solution=solution,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )
    else:
        logger.debug(f"Skipped adding {ENTRY_POINTS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeGroup)
        and CONNECTORS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        connections_agg = defaultdict(list)
        for sub_graph_group_item in recurse_layers(graph_group_item):
            connections = get_connections(
                connections_layer_tree_node=sub_graph_group_item,
            )

            for k, v in connections.items():
                connections_agg[k].extend(v)

        assemble_connections(
            connections_agg,
            solution,
            graph_key,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )
    else:
        logger.debug(f"Skipped adding {CONNECTORS_GROUP_DESCRIPTOR}")


def add_flat_route_element_layers(
    collect_errors,
    collect_invalid,
    collect_warnings,
    graph_group_item,
    graph_key,
    issues,
    solution,
):
    if (
        isinstance(graph_group_item, QgsLayerTreeLayer)
        and DOORS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        add_doors(
            graph_key=graph_key,
            door_layer_tree_node=graph_group_item,
            solution=solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )
    else:
        logger.debug(f"Skipped adding {DOORS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeLayer)
        and BARRIERS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        add_barriers(
            graph_key=graph_key,
            barrier_layer_tree_node=graph_group_item,
            solution=solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )
    else:
        logger.debug(f"Skipped adding {BARRIERS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeLayer)
        and AVOIDS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        add_avoids(
            graph_key=graph_key,
            avoid_layer_tree_node=graph_group_item,
            solution=solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )
    else:
        logger.debug(f"Skipped adding {AVOIDS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeLayer)
        and PREFERS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        add_prefers(
            graph_key=graph_key,
            prefer_layer_tree_node=graph_group_item,
            solution=solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )
    else:
        logger.debug(f"Skipped adding {PREFERS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeLayer)
        and OBSTACLES_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        add_obstacles(
            graph_key=graph_key,
            obstacle_layer_tree_node=graph_group_item,
            solution=solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )
    else:
        logger.debug(f"Skipped adding {OBSTACLES_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeLayer)
        and ENTRY_POINTS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        add_entry_points(
            graph_key=graph_key,
            entry_point_layer_tree_node=graph_group_item,
            solution=solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )
    else:
        logger.debug(f"Skipped adding {ENTRY_POINTS_GROUP_DESCRIPTOR}")
    if (
        isinstance(graph_group_item, QgsLayerTreeLayer)
        and CONNECTORS_GROUP_DESCRIPTOR in graph_group_item.name()
    ):
        connections = get_connections(
            connections_layer_tree_node=graph_group_item,
        )
        assemble_connections(
            connections,
            solution,
            graph_key,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )
    else:
        logger.debug(f"Skipped adding {CONNECTORS_GROUP_DESCRIPTOR}")


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
            connectors.append(
                Connector(
                    admin_id=external_id,
                    floor_index=floor_index,
                    point=prepare_geom_for_mi_db(geom),
                )
            )

        try:
            connector_key = solution.add_connection(
                connection_id,
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
