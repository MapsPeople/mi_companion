import logging
from collections import defaultdict
from typing import Any, List, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import (
    Solution,
)
from jord.qgis_utilities import recurse_layers
from mi_companion import (
    MAKE_FLOOR_WISE_LAYERS,
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
from .parse_avoids import add_avoids
from .parse_barriers import add_barriers
from .parse_connections import assemble_connections, get_connections
from .parse_doors import add_doors
from .parse_entry_points import add_entry_points
from .parse_obstacles import add_obstacles
from .parse_prefers import add_prefers

logger = logging.getLogger(__name__)

__all__ = [
    "add_route_elements",
]


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
