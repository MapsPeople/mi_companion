import logging
from typing import Any, Optional

from integration_system.model import Building, Floor, Solution
from jord.qgis_utilities import (
    Qgis3dCullingMode,
    Qgis3dFacade,
    make_field_unique,
    set_3d_view_settings,
    set_geometry_constraints,
)
from jord.qlive_utilities import add_shapely_layer
from mi_companion import (
    DESCRIPTOR_BEFORE,
    FLOOR_HEIGHT,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.constants import (
    FLOOR_VERTICAL_SPACING,
    INSERT_INDEX,
)
from mi_companion.layer_descriptors import (
    FLOOR_GROUP_DESCRIPTOR,
    FLOOR_POLYGON_DESCRIPTOR,
)
from .location import add_floor_content_layers
from .parsing import translations_to_flattened_dict
from ...projection import (
    prepare_geom_for_qgis,
    solve_target_crs_authid,
)

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
            if DESCRIPTOR_BEFORE:
                floor_name = (
                    f"{descriptor} {floor.translations[solution.default_language].name}"
                )
            else:
                floor_name = (
                    f"{floor.translations[solution.default_language].name} {descriptor}"
                )

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
                            "floor_index": floor.floor_index,
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
                    geoms=[prepare_geom_for_qgis(floor.polygon)],
                    name=FLOOR_POLYGON_DESCRIPTOR,
                    columns=[
                        {
                            "external_id": floor.external_id,
                            "floor_index": floor.floor_index,
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
