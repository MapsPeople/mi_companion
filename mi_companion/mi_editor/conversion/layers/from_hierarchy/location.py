import logging
import uuid
from typing import Any, Optional

import shapely

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import LocationType, Solution
from mi_companion.configuration.constants import DEFAULT_CUSTOM_PROPERTIES, VERBOSE
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.custom_props import (
    extract_custom_props,
)
from mi_companion.mi_editor.conversion.layers.type_enums import LocationTypeEnum

__all__ = ["add_floor_contents"]

from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)
# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant


def add_floor_locations(
    location_group_items: Any,
    solution: Solution,
    floor_key: str,
    location_type: LocationTypeEnum,
) -> None:
    layer = location_group_items.layer()
    if layer:
        for layer_feature in layer.getFeatures():
            feature_attributes = {
                k.name(): v
                for k, v in zip(
                    layer_feature.fields(),
                    layer_feature.attributes(),
                )
            }

            location_type_name = feature_attributes["location_type.name"]
            if isinstance(location_type_name, str):
                ...
            elif isinstance(location_type_name, QVariant):
                # logger.warning(f"{typeToDisplayString(type(v))}")
                if location_type_name.isNull():  # isNull(v):
                    location_type_name = None
                else:
                    location_type_name = location_type_name.value()

            location_type_key = LocationType.compute_key(name=location_type_name)
            if solution.location_types.get(location_type_key) is None:
                if read_bool_setting(
                    "ALLOW_LOCATION_TYPE_CREATION"
                ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                    location_type_key = solution.add_location_type(location_type_name)
                else:
                    raise ValueError(
                        f"{location_type_key} is not a valid location type"
                    )

            custom_props = extract_custom_props(feature_attributes)

            admin_id = feature_attributes["admin_id"]
            external_id = feature_attributes["external_id"]
            if external_id is None:
                if read_bool_setting("GENERATE_MISSING_EXTERNAL_IDS"):
                    external_id = uuid.uuid4().hex
                else:
                    raise ValueError(f"{layer_feature} is missing a valid external id")

            name = feature_attributes["name"]

            if name is None:
                name = external_id

            feature_geom = layer_feature.geometry()
            if feature_geom is not None:
                geom_wkb = feature_geom.asWkb()
                if geom_wkb is not None:
                    geom_shapely = shapely.from_wkb(geom_wkb)
                    if geom_shapely is not None:
                        common_kvs = dict(
                            admin_id=admin_id,
                            external_id=external_id,
                            name=name,
                            floor_key=floor_key,
                            location_type_key=location_type_key,
                            custom_properties=(
                                custom_props
                                if custom_props
                                else DEFAULT_CUSTOM_PROPERTIES
                            ),
                        )

                        if location_type == LocationTypeEnum.ROOM:
                            room_key = solution.add_room(
                                polygon=prepare_geom_for_mi_db(geom_shapely),
                                **common_kvs,
                            )
                        elif location_type == LocationTypeEnum.AREA:
                            room_key = solution.add_area(
                                polygon=prepare_geom_for_mi_db(geom_shapely),
                                **common_kvs,
                            )
                        elif location_type == LocationTypeEnum.POI:
                            room_key = solution.add_point_of_interest(
                                point=prepare_geom_for_mi_db(geom_shapely), **common_kvs
                            )
                        else:
                            raise Exception(f"{location_type=} is unknown")
                        if VERBOSE:
                            logger.info(f"added {location_type} {room_key}")


def add_floor_contents(
    *,
    floor_group_items: QgsLayerTreeGroup,
    floor_key: str,
    solution: Solution,
    graph_key: Optional[str] = None,
    floor_index: Optional[int] = None,
) -> None:
    for location_group_items in floor_group_items.children():
        if (
            isinstance(location_group_items, QgsLayerTreeLayer)
            and LocationTypeEnum.ROOM.value in location_group_items.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_items, solution, floor_key, LocationTypeEnum.ROOM
            )

        if (
            isinstance(location_group_items, QgsLayerTreeLayer)
            and LocationTypeEnum.POI.value in location_group_items.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_items, solution, floor_key, LocationTypeEnum.POI
            )

        if (
            isinstance(location_group_items, QgsLayerTreeLayer)
            and LocationTypeEnum.AREA.value in location_group_items.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_items, solution, floor_key, LocationTypeEnum.AREA
            )
