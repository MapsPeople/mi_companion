import logging
from typing import Any, Callable, Optional

from integration_system.mi import get_outside_building_admin_id
from integration_system.model import Building, Solution, Venue
from jord.qgis_utilities import make_field_unique, set_geometry_constraints
from jord.qlive_utilities import add_shapely_layer
from mi_companion import (
    DESCRIPTOR_BEFORE,
    HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS,
)
from mi_companion.layer_descriptors import (
    BUILDING_GROUP_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
)
from .floor import add_floor_layers

__all__ = ["add_building_layers"]

from ...projection import (
    prepare_geom_for_qgis,
    solve_target_crs_authid,
)
from mi_companion.constants import (
    INSERT_INDEX,
    SHOW_FLOOR_LAYERS_ON_LOAD,
)

logger = logging.getLogger(__name__)


def add_building_layers(
    *,
    solution: Solution,
    venue: Venue,
    venue_group: Any,
    qgis_instance_handle: Any,
    location_type_ref_layer: Optional[Any] = None,
    location_type_dropdown_widget: Optional[Any] = None,
    occupant_dropdown_widget: Optional[Any] = None,
    progress_bar: Optional[Callable] = None,
) -> None:
    num_buildings = float(len(solution.buildings))

    for ith, building in enumerate(
        sorted(solution.buildings, key=lambda building_: building_.name)
    ):
        building: Building

        if progress_bar:
            progress_bar.setValue(int(20 + (float(ith) / num_buildings) * 80))

        is_outside_building = (
            get_outside_building_admin_id(venue.admin_id) == building.admin_id
        )
        floor_poly_layer_should_be_visible = SHOW_FLOOR_LAYERS_ON_LOAD

        if is_outside_building:
            floor_poly_layer_should_be_visible = False

        if HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS and is_outside_building:
            add_floor_layers(
                location_type_ref_layer=location_type_ref_layer,
                location_type_dropdown_widget=location_type_dropdown_widget,
                occupant_dropdown_widget=occupant_dropdown_widget,
                building=building,
                building_group=venue_group,
                qgis_instance_handle=qgis_instance_handle,
                solution=solution,
                visible=floor_poly_layer_should_be_visible,
            )

        elif building.venue.key == venue.key:
            if DESCRIPTOR_BEFORE:
                building_name = f"{BUILDING_GROUP_DESCRIPTOR} {building.name}"
            else:
                building_name = f"{building.name} {BUILDING_GROUP_DESCRIPTOR}"

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
                crs=solve_target_crs_authid(),
            )

            make_field_unique(building_layer, field_name="admin_id")
            set_geometry_constraints(building_layer)

            add_floor_layers(
                location_type_ref_layer=location_type_ref_layer,
                location_type_dropdown_widget=location_type_dropdown_widget,
                occupant_dropdown_widget=occupant_dropdown_widget,
                building=building,
                building_group=building_group,
                qgis_instance_handle=qgis_instance_handle,
                solution=solution,
                visible=floor_poly_layer_should_be_visible,
            )
        else:
            ...
            # logger.error("SKIP!")
