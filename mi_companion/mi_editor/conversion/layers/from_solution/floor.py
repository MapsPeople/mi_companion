import logging
from typing import Any, Optional

from jord.qgis_utilities import (
    Qgis3dCullingMode,
    Qgis3dFacade,
    make_field_unique,
    set_3d_view_settings,
    set_geometry_constraints,
    set_layer_rendering_scale,
)
from jord.qlive_utilities import add_shapely_layer
from mi_companion import (
    DESCRIPTOR_BEFORE,
    FLOOR_HEIGHT,
)
from mi_companion.configuration import read_bool_setting, read_float_setting
from mi_companion.constants import (
    ANCHOR_AS_INDIVIDUAL_FIELDS,
    FLOOR_VERTICAL_SPACING,
    INSERT_INDEX,
)
from mi_companion.layer_descriptors import (
    FLOOR_GROUP_DESCRIPTOR,
    FLOOR_POLYGON_DESCRIPTOR,
)
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_editing_qgis,
    solve_target_crs_authid,
)
from mi_companion.qgis_utilities import auto_center_anchors_when_outside
from sync_module.model import Building, Floor, Solution
from .location import add_floor_content_layers
from .parsing import translations_to_flattened_dict
from ...styling import add_rotation_scale_geometry_generator

logger = logging.getLogger(__name__)

__all__ = ["add_floor_layers"]


def add_floor_layers(
    *,
    location_type_ref_layer: Optional[Any] = None,
    location_type_dropdown_widget: Optional[Any] = None,
    occupant_dropdown_widget: Optional[Any] = None,
    building: Building,
    building_group: Any,
    qgis_instance_handle: Any,
    solution: Solution,
    visible: bool = True,
    # add_floor_polygon_geometry: bool = True,
) -> None:
    building_bottom_floor_tracker = {}
    for floor in sorted(solution.floors, key=lambda floor: floor.floor_index):
        floor: Floor
        if floor.building.key == building.key:
            descriptor = f"{FLOOR_GROUP_DESCRIPTOR}:{floor.floor_index}"

            if (
                solution.default_language in floor.translations
            ):  # SPECIAL CASE HANDLING FOR OUTSIDE BUILDING
                floor_name__ = floor.translations[solution.default_language].name
            else:
                floor_name__ = floor.translations["en"].name

            if DESCRIPTOR_BEFORE:
                floor_name = f"{descriptor} {floor_name__}"
            else:
                floor_name = f"{floor_name__} {descriptor}"

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

            anchor_fields = {}
            anch = prepare_geom_for_editing_qgis(floor.anchor)
            if ANCHOR_AS_INDIVIDUAL_FIELDS:
                anchor_fields["anchor_x"] = anch.x
                anchor_fields["anchor_y"] = anch.y

            else:
                anchor_fields["anchor"] = anch

            if INSERT_INDEX == 0:
                floor_layer = add_shapely_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    geoms=[prepare_geom_for_editing_qgis(floor.polygon)],
                    name=FLOOR_POLYGON_DESCRIPTOR,
                    columns=[
                        {
                            "external_id": floor.external_id,
                            "floor_index": floor.floor_index,
                            **anchor_fields,
                            **translations_to_flattened_dict(floor.translations),
                        }
                    ],
                    group=floor_group,
                    visible=visible,
                    crs=solve_target_crs_authid(),
                )

            add_floor_content_layers(
                qgis_instance_handle=qgis_instance_handle,
                solution=solution,
                floor=floor,
                floor_group=floor_group,
                location_type_ref_layer=location_type_ref_layer,
                location_type_dropdown_widget=location_type_dropdown_widget,
                occupant_dropdown_widget=occupant_dropdown_widget,
            )

            if INSERT_INDEX > 0:
                floor_layer = add_shapely_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    geoms=[prepare_geom_for_editing_qgis(floor.polygon)],
                    name=FLOOR_POLYGON_DESCRIPTOR,
                    columns=[
                        {
                            "external_id": floor.external_id,
                            "floor_index": floor.floor_index,
                            "anchor": prepare_geom_for_editing_qgis(floor.anchor),
                            **translations_to_flattened_dict(floor.translations),
                        }
                    ],
                    group=floor_group,
                    visible=visible,
                    crs=solve_target_crs_authid(),
                )

            assert floor_layer is not None
            make_field_unique(floor_layer, field_name="admin_id")
            set_3d_view_settings(
                floor_layer,
                offset=(FLOOR_VERTICAL_SPACING + FLOOR_HEIGHT) * floor.floor_index,
                extrusion=FLOOR_VERTICAL_SPACING,
                facades=Qgis3dFacade.walls_and_roofs,
                culling_mode=Qgis3dCullingMode.no_culling,
                color=(111, 111, 111),
            )
            set_geometry_constraints(floor_layer)
            # TODO: Use SolutionItem Annotations for field constraints

            set_layer_rendering_scale(
                floor_layer,
                min_ratio=read_float_setting("LAYER_GEOM_VISIBLE_MIN_RATIO"),
            )

            auto_center_anchors_when_outside(floor_layer)
            add_rotation_scale_geometry_generator(floor_layer)
