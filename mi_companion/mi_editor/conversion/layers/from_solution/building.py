import logging
from typing import Optional, Any

from jord.qlive_utilities import add_shapely_layer

from mi_companion.configuration.constants import (
    BUILDING_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
)
from .fields import make_field_unique
from .floor import add_floor_layers

__all__ = ["add_building_layers"]

from ...projection import (
    prepare_geom_for_qgis,
    GDS_EPSG_NUMBER,
    should_reproject,
    MI_EPSG_NUMBER,
    INSERT_INDEX,
)

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
                INSERT_INDEX + 1,  # 1+ for GRAPH
                f"{building.name} {BUILDING_DESCRIPTOR}",
            )
            building_group.setExpanded(True)
            building_group.setExpanded(False)

            building_layer = add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[prepare_geom_for_qgis(building.polygon)],
                name=BUILDING_POLYGON_DESCRIPTOR,
                columns=[{"external_id": building.external_id, "name": building.name}],
                group=building_group,
                visible=False,
                crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
            )
            make_field_unique(building_layer)

            add_floor_layers(
                available_location_type_map_widget,
                building,
                building_group,
                door_type_dropdown_widget,
                qgis_instance_handle,
                solution,
                venue,
            )
