import logging

from jord.qgis_utilities import read_plugin_setting
from jord.qlive_utilities import add_shapely_layer

from mi_companion import PROJECT_NAME, DEFAULT_PLUGIN_SETTINGS
from mi_companion.configuration.constants import (
    FLOOR_DESCRIPTOR,
    FLOOR_POLYGON_DESCRIPTOR,
)
from .location import add_floor_content_layers

logger = logging.getLogger(__name__)

__all__ = ["add_floor_layers"]


def add_floor_layers(
    available_location_type_map_widget,
    building,
    building_group,
    door_type_dropdown_widget,
    qgis_instance_handle,
    solution,
    venue,
):
    building_bottom_floor_tracker = {}
    for floor in sorted(solution.floors, key=lambda floor: floor.floor_index):
        if floor.building.external_id == building.external_id:
            floor_name = f"{floor.name} {FLOOR_DESCRIPTOR}"
            floor_group = building_group.insertGroup(
                0, floor_name
            )  # MutuallyExclusive = True # TODO: Maybe only show on floor at a time?
            floor_group.setExpanded(True)
            floor_group.setExpanded(False)

            if read_plugin_setting(
                "ONLY_SHOW_FIRST_FLOOR",
                default_value=DEFAULT_PLUGIN_SETTINGS["ONLY_SHOW_FIRST_FLOOR"],
                project_name=PROJECT_NAME,
            ):  # Only make first floor of building visible
                if (
                    building_group.name in building_bottom_floor_tracker
                ):  # TODO: IMPLEMENT PROPER COMPARISON
                    building_group.findGroup(floor_name).setItemVisibilityChecked(False)
                else:
                    building_bottom_floor_tracker[building_group.name] = (
                        floor.floor_index
                    )

            add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[floor.polygon],
                name=FLOOR_POLYGON_DESCRIPTOR,
                columns=[
                    {
                        "external_id": floor.external_id,
                        "name": floor.name,
                        "floor_index": floor.floor_index,
                    }
                ],
                group=floor_group,
                visible=False,
            )

            add_floor_content_layers(
                qgis_instance_handle=qgis_instance_handle,
                solution=solution,
                floor=floor,
                floor_group=floor_group,
                venue=venue,
                available_location_type_map_widget=available_location_type_map_widget,
                door_type_dropdown_widget=door_type_dropdown_widget,
            )
