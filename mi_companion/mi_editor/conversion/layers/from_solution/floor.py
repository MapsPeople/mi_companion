import logging
from typing import Any

from jord.qlive_utilities import add_shapely_layer

from integration_system.model import Building, Floor, Solution
from mi_companion.configuration.constants import (
    FLOOR_DESCRIPTOR,
    FLOOR_POLYGON_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from .fields import make_field_unique
from .location import add_floor_content_layers
from ...projection import (
    GDS_EPSG_NUMBER,
    INSERT_INDEX,
    MI_EPSG_NUMBER,
    prepare_geom_for_qgis,
    should_reproject,
)

logger = logging.getLogger(__name__)

__all__ = ["add_floor_layers"]


def add_floor_layers(
    available_location_type_map_widget: Any,
    building: Building,
    building_group: Any,
    qgis_instance_handle: Any,
    solution: Solution,
    # add_floor_polygon_geometry: bool = True,
) -> None:
    building_bottom_floor_tracker = {}
    for floor in sorted(solution.floors, key=lambda floor: floor.floor_index):
        floor: Floor
        if floor.building.key == building.key:
            floor_name = f"{floor.name} {FLOOR_DESCRIPTOR}:{floor.floor_index}"
            floor_group = building_group.insertGroup(
                INSERT_INDEX, floor_name
            )  # MutuallyExclusive = True # TODO: Maybe only show on floor at a time?
            floor_group.setExpanded(True)
            floor_group.setExpanded(False)

            if read_bool_setting(
                "ONLY_SHOW_FIRST_FLOOR"
            ):  # Only make first floor of building visible
                if (
                    building_group.name in building_bottom_floor_tracker
                ):  # TODO: IMPLEMENT PROPER COMPARISON
                    building_group.findGroup(floor_name).setItemVisibilityChecked(False)
                else:
                    building_bottom_floor_tracker[building_group.name] = (
                        floor.floor_index
                    )

            floor_layer = None
            if INSERT_INDEX == 0:
                floor_layer = add_shapely_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    geoms=[prepare_geom_for_qgis(floor.polygon)],
                    name=FLOOR_POLYGON_DESCRIPTOR,
                    columns=[
                        {
                            "external_id": floor.external_id,
                            "name": floor.name,
                            "floor_index": floor.floor_index,
                            **(
                                {
                                    f"custom_properties.{lang}.{prop}": str(v)
                                    for lang, props_map in floor.custom_properties.items()
                                    for prop, v in props_map.items()
                                }
                                if floor.custom_properties
                                else {}
                            ),
                        }
                    ],
                    group=floor_group,
                    visible=False,
                    crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
                )

            add_floor_content_layers(
                qgis_instance_handle=qgis_instance_handle,
                solution=solution,
                floor=floor,
                floor_group=floor_group,
                available_location_type_map_widget=available_location_type_map_widget,
            )

            if INSERT_INDEX > 0:
                floor_layer = add_shapely_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    geoms=[prepare_geom_for_qgis(floor.polygon)],
                    name=FLOOR_POLYGON_DESCRIPTOR,
                    columns=[
                        {
                            "external_id": floor.external_id,
                            "name": floor.name,
                            "floor_index": floor.floor_index,
                            **(
                                {
                                    f"custom_properties.{lang}.{prop}": str(v)
                                    for lang, props_map in floor.custom_properties.items()
                                    for prop, v in props_map.items()
                                }
                                if floor.custom_properties
                                else {}
                            ),
                        }
                    ],
                    group=floor_group,
                    visible=False,
                    crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
                )

            assert floor_layer is not None
            make_field_unique(floor_layer)
