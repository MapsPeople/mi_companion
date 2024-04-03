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
)

__all__ = ["add_floor_inventory"]


logger = logging.getLogger(__name__)


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
            and "rooms" in inventory_group_items.name()
            and floor_key is not None
        ):
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
                    if (
                        ALLOW_LOCATION_CREATION
                    ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                        location_type_key = solution.add_location_type(
                            location_type_name
                        )
                    else:
                        raise ValueError(
                            f"{location_type_key} is not a valid location type"
                        )

                external_id = room_attributes["external_id"]
                if external_id is None:
                    if GENERATE_MISSING_EXTERNAL_IDS:
                        external_id = uuid.uuid4().hex
                    else:
                        raise ValueError(
                            f"{room_feature} is missing a valid external id"
                        )

                name = room_attributes["name"]
                if name is None:
                    name = external_id
                # TODO: ADD CUSTOM PROPERTIES BACK!!!
                room_key = solution.add_room(
                    external_id=external_id,
                    name=name,
                    polygon=clean_shape(
                        shapely.from_wkt(room_feature.geometry().asWkt())
                    ),
                    floor_key=floor_key,
                    location_type_key=location_type_key,
                )
                if VERBOSE:
                    logger.info("added room", room_key)

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
            and "pois" in inventory_group_items.name()
            and floor_key is not None
        ):
            poi_point_layer = inventory_group_items.layer()
            for poi_feature in poi_point_layer.getFeatures():
                poi_attributes = {
                    k.name(): v
                    for k, v in zip(
                        poi_feature.fields(),
                        poi_feature.attributes(),
                    )
                }

                location_type_name = poi_attributes["location_type.name"]
                location_type_key = LocationType.compute_key(location_type_name)
                if solution.location_types.get(location_type_key) is None:
                    if (
                        ALLOW_LOCATION_CREATION
                    ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                        location_type_key = solution.add_location_type(
                            location_type_name
                        )
                    else:
                        raise ValueError(
                            f"{location_type_key} is not a valid location type"
                        )

                external_id = poi_attributes["external_id"]
                if external_id is None:
                    if GENERATE_MISSING_EXTERNAL_IDS:
                        external_id = uuid.uuid4().hex
                    else:
                        raise ValueError(
                            f"{poi_feature} is missing a valid external id"
                        )

                name = poi_attributes["name"]
                if name is None:
                    name = external_id
                # TODO: ADD CUSTOM PROPERTIES BACK!!!
                poi_key = solution.add_point_of_interest(
                    external_id=external_id,
                    name=name,
                    point=clean_shape(shapely.from_wkt(poi_feature.geometry().asWkt())),
                    floor_key=floor_key,
                    location_type_key=location_type_key,
                )
                if VERBOSE:
                    logger.info("added poi", poi_key)

        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and "areas" in inventory_group_items.name()
            and floor_key is not None
        ):
            doors_linestring_layer = inventory_group_items.layer()
            for area_feature in doors_linestring_layer.getFeatures():
                area_attributes = {
                    k.name(): v
                    for k, v in zip(
                        area_feature.fields(),
                        area_feature.attributes(),
                    )
                }
                # TODO: ADD CUSTOM PROPERTIES BACK!!!
                location_type_name = area_attributes["location_type.name"]
                location_type_key = LocationType.compute_key(location_type_name)
                if solution.location_types.get(location_type_key) is None:
                    if (
                        ALLOW_LOCATION_CREATION
                    ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                        location_type_key = solution.add_location_type(
                            location_type_name
                        )
                    else:
                        raise ValueError(
                            f"{location_type_key} is not a valid location type"
                        )

                external_id = area_attributes["external_id"]
                if external_id is None:
                    if GENERATE_MISSING_EXTERNAL_IDS:
                        external_id = uuid.uuid4().hex
                    else:
                        raise ValueError(
                            f"{area_feature} is missing a valid external id"
                        )

                name = area_attributes["name"]
                if name is None:
                    name = external_id

                area_key = solution.add_area(
                    external_id=external_id,
                    name=name,
                    polygon=clean_shape(
                        shapely.from_wkt(area_feature.geometry().asWkt())
                    ),
                    floor_key=floor_key,
                    location_type_key=location_type_key,
                )

                if VERBOSE:
                    logger.info("added area", area_key)
