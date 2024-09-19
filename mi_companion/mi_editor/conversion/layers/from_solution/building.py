import logging
from typing import Any, Optional

from jord.qgis_utilities.fields import make_field_unique
from jord.qlive_utilities import add_shapely_layer

from integration_system.mi import get_outside_building_admin_id
from integration_system.model import Building, Solution, Venue
from mi_companion import (
    BUILDING_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
    DESCRIPTOR_BEFORE,
    HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS,
)
from .floor import add_floor_layers

__all__ = ["add_building_layers"]

from ...projection import (
    prepare_geom_for_qgis,
    should_reproject,
)
from mi_companion.constants import (
    GDS_EPSG_NUMBER,
    INSERT_INDEX,
    MI_EPSG_NUMBER,
)

logger = logging.getLogger(__name__)


def add_building_layers(
    *,
    solution: Solution,
    venue: Venue,
    venue_group: Any,
    qgis_instance_handle: Any,
    available_location_type_map_widget: Optional[Any] = None,
    progress_bar: Optional[callable] = None,
) -> None:
    num_buildings = float(len(solution.buildings))

    for ith, building in enumerate(
        sorted(solution.buildings, key=lambda building_: building_.name)
    ):
        building: Building

        if progress_bar:
            progress_bar.setValue(int(20 + (float(ith) / num_buildings) * 80))

        if (
            HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS
            and get_outside_building_admin_id(venue.admin_id) == building.admin_id
        ):
            add_floor_layers(
                available_location_type_map_widget=available_location_type_map_widget,
                building=building,
                building_group=venue_group,
                qgis_instance_handle=qgis_instance_handle,
                solution=solution,
            )

        elif building.venue.key == venue.key:
            if DESCRIPTOR_BEFORE:
                building_name = f"{BUILDING_DESCRIPTOR} {building.name}"
            else:
                building_name = f"{building.name} {BUILDING_DESCRIPTOR}"

            building_group = venue_group.insertGroup(
                INSERT_INDEX,
                building_name,
            )

            building_group.setExpanded(True)
            building_group.setExpanded(False)

            building_layer = add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[prepare_geom_for_qgis(building.polygon)],
                name=BUILDING_POLYGON_DESCRIPTOR,
                columns=[
                    {
                        "admin_id": building.admin_id,
                        "external_id": building.external_id,
                        "name": building.name,
                        **(
                            {
                                f"custom_properties.{lang}.{prop}": str(v)
                                for lang, props_map in building.custom_properties.items()
                                for prop, v in props_map.items()
                            }
                            if building.custom_properties
                            else {}
                        ),
                    }
                ],
                group=building_group,
                visible=False,
                crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
            )

            make_field_unique(building_layer)

            add_floor_layers(
                available_location_type_map_widget=available_location_type_map_widget,
                building=building,
                building_group=building_group,
                qgis_instance_handle=qgis_instance_handle,
                solution=solution,
            )
        else:
            ...
            # logger.error("SKIP!")
