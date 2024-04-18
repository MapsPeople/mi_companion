import logging
import uuid

import shapely
from jord.shapely_utilities.base import clean_shape

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import Solution, LocationType
from mi_companion.configuration.constants import (
    VERBOSE,
    ALLOW_LOCATION_CREATION,
    ADD_DOORS,
    GENERATE_MISSING_EXTERNAL_IDS,
    DEFAULT_CUSTOM_PROPERTIES,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.custom_props import (
    extract_custom_props,
)
from mi_companion.mi_editor.conversion.layers.type_enums import InventoryTypeEnum

__all__ = ["add_floor_inventory"]


logger = logging.getLogger(__name__)


def add_inventory_type(
    inventory_group_items, solution, floor_key, inventory_type: InventoryTypeEnum
) -> None:
    room_polygon_layer = inventory_group_items.layer()
    for room_feature in room_polygon_layer.getFeatures():
        room_attributes = {
            k.name(): v
            for k, v in zip(
                room_feature.fields(),
                room_feature.attributes(),
            )
        }

        location_type_name = room_attributes["location_type.name"]
        location_type_key = LocationType.compute_key(location_type_name)
        if solution.location_types.get(location_type_key) is None:
            if ALLOW_LOCATION_CREATION:  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                location_type_key = solution.add_location_type(location_type_name)
            else:
                raise ValueError(f"{location_type_key} is not a valid location type")

        custom_props = extract_custom_props(room_attributes)

        external_id = room_attributes["external_id"]
        if external_id is None:
            if GENERATE_MISSING_EXTERNAL_IDS:
                external_id = uuid.uuid4().hex
            else:
                raise ValueError(f"{room_feature} is missing a valid external id")

        name = room_attributes["name"]

        if name is None:
            name = external_id

        room_key = None
        if inventory_type == InventoryTypeEnum.ROOM:
            room_key = solution.add_room(
                external_id=external_id,
                name=name,
                polygon=clean_shape(shapely.from_wkt(room_feature.geometry().asWkt())),
                floor_key=floor_key,
                location_type_key=location_type_key,
                custom_properties=(
                    custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                ),
            )
        elif inventory_type == InventoryTypeEnum.AREA:
            room_key = solution.add_area(
                external_id=external_id,
                name=name,
                polygon=clean_shape(shapely.from_wkt(room_feature.geometry().asWkt())),
                floor_key=floor_key,
                location_type_key=location_type_key,
                custom_properties=(
                    custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                ),
            )
        elif inventory_type == InventoryTypeEnum.POI:
            room_key = solution.add_point_of_interest(
                external_id=external_id,
                name=name,
                point=clean_shape(shapely.from_wkt(room_feature.geometry().asWkt())),
                floor_key=floor_key,
                location_type_key=location_type_key,
                custom_properties=(
                    custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                ),
            )
        else:
            raise Exception(f"{inventory_type=} is unknown")
        if VERBOSE:
            logger.info(f"added {inventory_type} {room_key}")


def add_floor_inventory(
    *,
    floor_group_items: QgsLayerTreeGroup,
    floor_key: str,
    graph_key: str,
    solution: Solution,
    floor_index: int,
) -> None:
    for inventory_group_items in floor_group_items.children():
        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and InventoryTypeEnum.ROOM.value in inventory_group_items.name()
            and floor_key is not None
        ):
            add_inventory_type(
                inventory_group_items, solution, floor_key, InventoryTypeEnum.ROOM
            )

        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and "doors" in inventory_group_items.name()
            and graph_key is not None
            and ADD_DOORS
        ):
            doors_linestring_layer = inventory_group_items.layer()
            for door_feature in doors_linestring_layer.getFeatures():
                door_attributes = {
                    k.name(): v
                    for k, v in zip(
                        door_feature.fields(),
                        door_feature.attributes(),
                    )
                }

                door_key = solution.add_door(
                    door_attributes["external_id"],
                    linestring=clean_shape(
                        shapely.from_wkt(door_feature.geometry().asWkt())
                    ),
                    door_type=door_attributes["door_type"],
                    floor_index=floor_index,
                    graph_key=graph_key,
                )
                if VERBOSE:
                    logger.info("added door", door_key)
        else:
            logger.error(
                f"Skipped adding doors because of "
                f"{isinstance(inventory_group_items, QgsLayerTreeLayer)=} "
                f'{"doors" in inventory_group_items.name()=} '
                f"{graph_key is not None=} "
                f"{ADD_DOORS=}"
            )

        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and InventoryTypeEnum.POI.value in inventory_group_items.name()
            and floor_key is not None
        ):
            add_inventory_type(
                inventory_group_items, solution, floor_key, InventoryTypeEnum.POI
            )

        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and InventoryTypeEnum.AREA.value in inventory_group_items.name()
            and floor_key is not None
        ):
            add_inventory_type(
                inventory_group_items, solution, floor_key, InventoryTypeEnum.AREA
            )
