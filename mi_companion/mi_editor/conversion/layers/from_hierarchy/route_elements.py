import logging
from typing import Any

import shapely

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import DoorType, Solution
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


def add_doors(
    *, floor_index: int, graph_key: str, location_group_items: Any, solution: Solution
) -> None:
    doors_linestring_layer = location_group_items.layer()
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
                shapely.from_wkt(door_feature.geometry().asWkt())
            ),
            door_type=DoorType.__getitem__(door_type),
            floor_index=floor_index,
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added door", door_key)


def add_barriers(
    floor_index: int, graph_key: str, location_group_items: Any, solution: Solution
) -> None:
    pass


def add_avoids(
    floor_index: int, graph_key: str, location_group_items: Any, solution: Solution
) -> None:
    pass


def add_prefers(
    floor_index: int, graph_key: str, location_group_items: Any, solution: Solution
) -> None:
    pass


def add_obstacles(
    floor_index: int, graph_key: str, location_group_items: Any, solution: Solution
) -> None:
    pass


def add_entry_points(
    floor_index: int, graph_key: str, location_group_items: Any, solution: Solution
) -> None:
    pass


def add_connections(
    floor_index: int, graph_key: str, location_group_items: Any, solution: Solution
) -> None:
    pass


def add_route_elements(
    graph_key: str, venue_group_item: Any, solution: Solution
) -> None:
    if read_bool_setting("ADD_ROUTE_ELEMENTS") and graph_key is not None:
        for ith_venue_group_item, location_group_items in enumerate(venue_group_item):
            if (
                isinstance(location_group_items, QgsLayerTreeLayer)
                and DOORS_DESCRIPTOR in location_group_items.name()
            ):
                add_doors(
                    graph_key=graph_key,
                    location_group_items=location_group_items,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {DOORS_DESCRIPTOR}")

            if (
                isinstance(location_group_items, QgsLayerTreeLayer)
                and BARRIERS_DESCRIPTOR in location_group_items.name()
            ):
                add_barriers(
                    graph_key=graph_key,
                    location_group_items=location_group_items,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {BARRIERS_DESCRIPTOR}")

            if (
                isinstance(location_group_items, QgsLayerTreeLayer)
                and AVOIDS_DESCRIPTOR in location_group_items.name()
            ):
                add_avoids(
                    graph_key=graph_key,
                    location_group_items=location_group_items,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {AVOIDS_DESCRIPTOR}")

            if (
                isinstance(location_group_items, QgsLayerTreeLayer)
                and PREFERS_DESCRIPTOR in location_group_items.name()
            ):
                add_prefers(
                    graph_key=graph_key,
                    location_group_items=location_group_items,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {PREFERS_DESCRIPTOR}")

            if (
                isinstance(location_group_items, QgsLayerTreeLayer)
                and OBSTACLES_DESCRIPTOR in location_group_items.name()
            ):
                add_obstacles(
                    graph_key=graph_key,
                    location_group_items=location_group_items,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {OBSTACLES_DESCRIPTOR}")

            if (
                isinstance(location_group_items, QgsLayerTreeLayer)
                and ENTRY_POINTS_DESCRIPTOR in location_group_items.name()
            ):
                add_entry_points(
                    graph_key=graph_key,
                    location_group_items=location_group_items,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {ENTRY_POINTS_DESCRIPTOR}")

            if (
                isinstance(location_group_items, QgsLayerTreeLayer)
                and CONNECTORS_DESCRIPTOR in location_group_items.name()
            ):
                add_connections(
                    graph_key=graph_key,
                    location_group_items=location_group_items,
                    solution=solution,
                )
            else:
                logger.debug(f"Skipped adding {CONNECTORS_DESCRIPTOR}")
