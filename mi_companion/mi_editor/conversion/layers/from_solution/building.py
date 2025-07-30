import logging
from typing import Any, Callable, Optional

from jord.qgis_utilities import (
    make_field_unique,
    set_geometry_constraints,
    set_layer_rendering_scale,
)
from jord.qlive_utilities import add_shapely_layer
from mi_companion import (
    DESCRIPTOR_BEFORE,
    HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS,
)
from mi_companion.configuration import read_float_setting
from mi_companion.constants import (
    ANCHOR_AS_INDIVIDUAL_FIELDS,
    INSERT_INDEX,
    SHOW_FLOOR_LAYERS_ON_LOAD,
)
from mi_companion.layer_descriptors import (
    BUILDING_GROUP_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
)
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_editing_qgis,
    solve_target_crs_authid,
)
from mi_companion.qgis_utilities import (
    auto_center_anchors_when_outside,
)
from sync_module.mi import get_outside_building_admin_id
from sync_module.model import Building, Solution, Venue
from sync_module.tools import translations_to_flattened_dict
from .floor import add_floor_layers
from ...styling import add_rotation_scale_geometry_generator

__all__ = ["add_building_layers"]


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
        sorted(
            solution.buildings,
            key=lambda building_: (
                building_.translations[solution.default_language].name
                if solution.default_language in building_.translations
                else building_.translations["en"].name
            ),
        )
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

            if (
                solution.default_language in building.translations
            ):  # SPECIAL CASE HANDLING FOR OUTSIDE BUILDING
                building_name__ = building.translations[solution.default_language].name
            else:
                building_name__ = building.translations["en"].name

            if DESCRIPTOR_BEFORE:
                building_name = f"{BUILDING_GROUP_DESCRIPTOR} {building_name__}"
            else:
                building_name = f"{building_name__} {BUILDING_GROUP_DESCRIPTOR}"

            building_group = venue_group.insertGroup(
                INSERT_INDEX,
                building_name,
            )

            building_group.setExpanded(True)
            building_group.setExpanded(False)

            anchor_fields = {}
            anch = prepare_geom_for_editing_qgis(building.anchor)
            if ANCHOR_AS_INDIVIDUAL_FIELDS:
                anchor_fields["anchor_x"] = anch.x
                anchor_fields["anchor_y"] = anch.y
            else:
                anchor_fields["anchor"] = anch

            building_layer = add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[prepare_geom_for_editing_qgis(building.polygon)],
                name=BUILDING_POLYGON_DESCRIPTOR,
                columns=[
                    {
                        "admin_id": building.admin_id,
                        "external_id": building.external_id,
                        **anchor_fields,
                        **translations_to_flattened_dict(building.translations),
                    }
                ],
                group=building_group,
                visible=False,
                crs=solve_target_crs_authid(),
            )

            auto_center_anchors_when_outside(building_layer)
            add_rotation_scale_geometry_generator(building_layer)

            make_field_unique(building_layer, field_name="admin_id")
            set_geometry_constraints(building_layer)

            set_layer_rendering_scale(
                building_layer,
                min_ratio=read_float_setting("LAYER_GEOM_VISIBLE_MIN_RATIO"),
            )

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
