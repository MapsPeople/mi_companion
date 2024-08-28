import logging
from collections import defaultdict
from typing import Any

import shapely

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import (
    ConnectionType,
    Connector,
    DoorType,
    EntryPointType,
    Solution,
)
from mi_companion.configuration.constants import (
    AVOIDS_DESCRIPTOR,
    BARRIERS_DESCRIPTOR,
    CONNECTORS_DESCRIPTOR,
    DOORS_DESCRIPTOR,
    ENTRY_POINTS_DESCRIPTOR,
    OBSTACLES_DESCRIPTOR,
    PREFERS_DESCRIPTOR,
    VERBOSE,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)

__all__ = ["add_doors"]


def add_doors(*, graph_key: str, door_layer_tree_node: Any, solution: Solution) -> None:
    doors_linestring_layer = door_layer_tree_node.layer()
    for door_feature in doors_linestring_layer.getFeatures():
        door_attributes = {
            k.name(): v
            for k, v in zip(
                door_feature.fields(),
                door_feature.attributes(),
            )
        }

        door_type = door_attributes["door_type"]

        if isinstance(door_type, str):
            ...
        elif isinstance(door_type, QVariant):
            # logger.warning(f"{typeToDisplayString(type(v))}")
            if door_type.isNull():  # isNull(v):
                door_type = None
            else:
                door_type = door_type.value()

        door_key = solution.add_door(
            door_attributes["external_id"],
            linestring=prepare_geom_for_mi_db(
                shapely.wkt.loads(door_feature.geometry().asWkt())
            ),
            door_type=DoorType(door_type),
            floor_index=int(door_attributes["floor_index"]),
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added door", door_key)


def add_barriers(
    graph_key: str, barrier_layer_tree_node: Any, solution: Solution
) -> None:
    barriers_linestring_layer = barrier_layer_tree_node.layer()
    for barrier_feature in barriers_linestring_layer.getFeatures():
        barrier_attributes = {
            k.name(): v
            for k, v in zip(
                barrier_feature.fields(),
                barrier_feature.attributes(),
            )
        }

        barrier_key = solution.add_barrier(
            barrier_attributes["external_id"],
            point=prepare_geom_for_mi_db(
                shapely.wkt.loads(barrier_feature.geometry().asWkt())
            ),
            floor_index=int(barrier_attributes["floor_index"]),
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added barrier", barrier_key)


def add_avoids(graph_key: str, avoid_layer_tree_node: Any, solution: Solution) -> None:
    avoids_linestring_layer = avoid_layer_tree_node.layer()
    for avoid_feature in avoids_linestring_layer.getFeatures():
        avoid_attributes = {
            k.name(): v
            for k, v in zip(
                avoid_feature.fields(),
                avoid_feature.attributes(),
            )
        }

        avoid_key = solution.add_avoid(
            avoid_attributes["external_id"],
            point=prepare_geom_for_mi_db(
                shapely.wkt.loads(avoid_feature.geometry().asWkt())
            ),
            floor_index=int(avoid_attributes["floor_index"]),
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added avoid", avoid_key)


def add_prefers(
    graph_key: str, prefer_layer_tree_node: Any, solution: Solution
) -> None:
    prefers_linestring_layer = prefer_layer_tree_node.layer()
    for prefer_feature in prefers_linestring_layer.getFeatures():
        prefer_attributes = {
            k.name(): v
            for k, v in zip(
                prefer_feature.fields(),
                prefer_feature.attributes(),
            )
        }

        prefer_key = solution.add_prefer(
            prefer_attributes["external_id"],
            point=prepare_geom_for_mi_db(
                shapely.wkt.loads(prefer_feature.geometry().asWkt())
            ),
            floor_index=int(prefer_attributes["floor_index"]),
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added prefer", prefer_key)


def add_obstacles(
    graph_key: str, obstacle_layer_tree_node: Any, solution: Solution
) -> None:
    obstacles_linestring_layer = obstacle_layer_tree_node.layer()
    for obstacle_feature in obstacles_linestring_layer.getFeatures():
        obstacle_attributes = {
            k.name(): v
            for k, v in zip(
                obstacle_feature.fields(),
                obstacle_feature.attributes(),
            )
        }

        obstacle_key = solution.add_obstacle(
            obstacle_attributes["external_id"],
            polygon=prepare_geom_for_mi_db(
                shapely.wkt.loads(obstacle_feature.geometry().asWkt())
            ),
            floor_index=int(obstacle_attributes["floor_index"]),
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added obstacle", obstacle_key)


def add_entry_points(
    graph_key: str, entry_point_layer_tree_node: Any, solution: Solution
) -> None:
    entry_points_linestring_layer = entry_point_layer_tree_node.layer()
    for entry_point_feature in entry_points_linestring_layer.getFeatures():
        entry_point_attributes = {
            k.name(): v
            for k, v in zip(
                entry_point_feature.fields(),
                entry_point_feature.attributes(),
            )
        }

        entry_point_type = entry_point_attributes["entry_point_type"]

        if isinstance(entry_point_type, str):
            ...
        elif isinstance(entry_point_type, QVariant):
            # logger.warning(f"{typeToDisplayString(type(v))}")
            if entry_point_type.isNull():  # isNull(v):
                entry_point_type = None
            else:
                entry_point_type = entry_point_type.value()

        entry_point_key = solution.add_entry_point(
            entry_point_attributes["external_id"],
            point=prepare_geom_for_mi_db(
                shapely.wkt.loads(entry_point_feature.geometry().asWkt())
            ),
            entry_point_type=EntryPointType(entry_point_type),
            floor_index=int(entry_point_attributes["floor_index"]),
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added entry_point", entry_point_key)


def add_connections(
    graph_key: str, connections_layer_tree_node: Any, solution: Solution
) -> None:  # TODO: FINISH!
    connectors_linestring_layer = connections_layer_tree_node.layer()
    connections = defaultdict(list)
    for connector_feature in connectors_linestring_layer.getFeatures():
        connector_attributes = {
            k.name(): v
            for k, v in zip(
                connector_feature.fields(),
                connector_feature.attributes(),
            )
        }

        connection_type = connector_attributes["connection_type"]
        connection_id = connector_attributes["connection_id"]
        connector_floor_index = connector_attributes["floor_index"]
        connector_external_id = connector_attributes["external_id"]

        if isinstance(connection_type, str):
            ...
        elif isinstance(connection_type, QVariant):
            # logger.warning(f"{typeToDisplayString(type(v))}")
            if connection_type.isNull():  # isNull(v):
                connection_type = None
            else:
                connection_type = connection_type.value()

        connector_geom = prepare_geom_for_mi_db(
            shapely.wkt.loads(connector_feature.geometry().asWkt())
        )
        connections[connection_id].append(
            (
                (connector_geom, connector_floor_index, connector_external_id),
                connection_type,
            )
        )

    for connection_id, connector_tuples in connections.items():
        inner_connector_tuples, connection_types = zip(*connector_tuples)

        connection_type_set = set(connection_types)
        assert (
            len(connection_type_set) == 1
        ), f"Connectors with {connection_id} has varying {connection_type_set}, this is not allowed"

        connection_type = next(iter(connection_type_set))

        connectors = []
        for geom, floor_index, external_id in inner_connector_tuples:
            connectors.append(
                Connector(external_id=external_id, floor_index=floor_index, point=geom)
            )

        connector_key = solution.add_connection(
            connection_id,
            connectors=connectors,
            connection_type=ConnectionType(connection_type),
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added connector", connector_key)


def add_route_elements(graph_key: str, graph_group: Any, solution: Solution) -> None:
    if read_bool_setting("ADD_ROUTE_ELEMENTS") and graph_key is not None:
        for ith_graph_group_item, graph_group_item in enumerate(graph_group.children()):
            if (
                isinstance(graph_group_item, QgsLayerTreeLayer)
                and DOORS_DESCRIPTOR in graph_group_item.name()
            ):
                add_doors(
                    graph_key=graph_key,
                    door_layer_tree_node=graph_group_item,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {DOORS_DESCRIPTOR}")

            if (
                isinstance(graph_group_item, QgsLayerTreeLayer)
                and BARRIERS_DESCRIPTOR in graph_group_item.name()
            ):
                add_barriers(
                    graph_key=graph_key,
                    barrier_layer_tree_node=graph_group_item,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {BARRIERS_DESCRIPTOR}")

            if (
                isinstance(graph_group_item, QgsLayerTreeLayer)
                and AVOIDS_DESCRIPTOR in graph_group_item.name()
            ):
                add_avoids(
                    graph_key=graph_key,
                    avoid_layer_tree_node=graph_group_item,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {AVOIDS_DESCRIPTOR}")

            if (
                isinstance(graph_group_item, QgsLayerTreeLayer)
                and PREFERS_DESCRIPTOR in graph_group_item.name()
            ):
                add_prefers(
                    graph_key=graph_key,
                    prefer_layer_tree_node=graph_group_item,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {PREFERS_DESCRIPTOR}")

            if (
                isinstance(graph_group_item, QgsLayerTreeLayer)
                and OBSTACLES_DESCRIPTOR in graph_group_item.name()
            ):
                add_obstacles(
                    graph_key=graph_key,
                    obstacle_layer_tree_node=graph_group_item,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {OBSTACLES_DESCRIPTOR}")

            if (
                isinstance(graph_group_item, QgsLayerTreeLayer)
                and ENTRY_POINTS_DESCRIPTOR in graph_group_item.name()
            ):
                add_entry_points(
                    graph_key=graph_key,
                    entry_point_layer_tree_node=graph_group_item,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {ENTRY_POINTS_DESCRIPTOR}")

            if (
                isinstance(graph_group_item, QgsLayerTreeLayer)
                and CONNECTORS_DESCRIPTOR in graph_group_item.name()
            ):
                add_connections(
                    graph_key=graph_key,
                    connections_layer_tree_node=graph_group_item,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {CONNECTORS_DESCRIPTOR}")
