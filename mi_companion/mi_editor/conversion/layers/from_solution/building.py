import logging
from typing import Optional, Any

from jord.qlive_utilities import add_shapely_layer

from mi_companion.configuration.constants import (
    BUILDING_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
)
from .floor import add_floor_layers

__all__ = ["add_building_layers"]


logger = logging.getLogger(__name__)


def add_building_layers(
    *,
    solution,
    venue,
    venue_group,
    qgis_instance_handle,
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

            add_floor_layers(
                available_location_type_map_widget,
                building,
                building_group,
                door_type_dropdown_widget,
                qgis_instance_handle,
                solution,
                venue,
            )
