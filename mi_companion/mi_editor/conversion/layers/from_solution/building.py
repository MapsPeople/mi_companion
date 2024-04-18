import logging
from typing import Optional, Any

from jord.qlive_utilities import add_shapely_layer

from mi_companion.configuration.constants import (
    FLOOR_DESCRIPTOR,
    BUILDING_DESCRIPTOR,
    FLOOR_POLYGON_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
    ONLY_SHOW_FIRST_FLOOR,
)
from .location import add_inventory_layers

__all__ = ["add_building_layers"]


logger = logging.getLogger(__name__)


def add_building_layers(
    *,
    solution,
    venue,
    venue_group,
    qgis_instance_handle,
    layer_tree_root,
    available_location_type_map_widget: Optional[Any] = None,
    door_type_dropdown_widget: Optional[Any] = None,
    progress_bar: Optional[callable] = None,
):
    num_buildings = float(len(solution.buildings))

    for ith, building in enumerate(
        sorted(solution.buildings, key=lambda building: building.name)
    ):
        if progress_bar:
            progress_bar.setValue(int(20 + (float(ith) / num_buildings) * 80))

        if building.venue.external_id == venue.external_id:
            building_group = venue_group.insertGroup(
                0, f"{building.name} {BUILDING_DESCRIPTOR}"
            )
            building_group.setExpanded(True)
            building_group.setExpanded(False)

            add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[building.polygon],
                name=BUILDING_POLYGON_DESCRIPTOR,
                columns=[{"external_id": building.external_id, "name": building.name}],
                group=building_group,
                visible=False,
            )

            building_bottom_floor_tracker = {}
            for floor in sorted(solution.floors, key=lambda floor: floor.floor_index):
                if floor.building.external_id == building.external_id:
                    floor_name = f"{floor.name} {FLOOR_DESCRIPTOR}"
                    floor_group = building_group.insertGroup(
                        0, floor_name
                    )  # MutuallyExclusive = True # TODO: Maybe only show on floor at a time?
                    floor_group.setExpanded(True)
                    floor_group.setExpanded(False)

                    if (
                        ONLY_SHOW_FIRST_FLOOR
                    ):  # Only make first floor of building visible
                        if (
                            building_group.name in building_bottom_floor_tracker
                        ):  # TODO: IMPLEMENT PROPER COMPARISON
                            building_group.findGroup(
                                floor_name
                            ).setItemVisibilityChecked(False)
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

                    add_inventory_layers(
                        qgis_instance_handle=qgis_instance_handle,
                        solution=solution,
                        floor=floor,
                        floor_group=floor_group,
                        venue=venue,
                        available_location_type_map_widget=available_location_type_map_widget,
                        door_type_dropdown_widget=door_type_dropdown_widget,
                    )
