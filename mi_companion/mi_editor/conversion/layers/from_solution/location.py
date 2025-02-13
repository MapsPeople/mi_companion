import logging

from jord.qgis_utilities.fields import (
    add_dropdown_widget,
    make_field_boolean,
    make_field_default,
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
)
from jord.qgis_utilities.styling import set3dviewsettings

from mi_companion.constants import (
    FLOOR_HEIGHT,
    FLOOR_VERTICAL_SPACING,
    USE_EXTERNAL_ID_FLOOR_SELECTION,
)
from .custom_props import process_custom_props_df, to_df
from ..type_enums import BackendLocationTypeEnum
from ...projection import (
    reproject_geometry_df,
    solve_target_crs_authid,
)

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum

from typing import Any, Iterable, List, Optional

import geopandas
from jord.qlive_utilities import add_dataframe_layer

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

from integration_system.model import (
    CollectionMixin,
    Floor,
    Solution,
)

__all__ = ["add_floor_content_layers"]

logger = logging.getLogger(__name__)

BOOLEAN_LOCATION_ATTRS = ("is_searchable", "is_active")
STR_LOCATION_ATTRS = ("description", "external_id", "name", "admin_id")
FLOAT_LOCATION_ATTRS = ()
INT_LOCATION_ATTRS = ()


class LocationGeometryType(StrEnum):
    point = "point"
    # linestring = "linestring"
    polygon = "polygon"


def add_location_layer(
    location_collection: CollectionMixin,
    name: str,
    geometry_column_name: LocationGeometryType,
    *,
    qgis_instance_handle: Any,
    floor_group: Any,
    floor: Floor,
    dropdown_widget: Optional[Any] = None,
) -> Optional[List[Any]]:  # QgsVectorLayer

    shape_df = to_df(location_collection)

    assert len(location_collection) == len(shape_df)
    if shape_df.empty:
        logger.warning(f"{name=} {shape_df=} was empty!")

        return

    # logger.info(f"adding {name=} with {len(collection_)} elements")

    if USE_EXTERNAL_ID_FLOOR_SELECTION:  # OLD WAY
        floor_selection = shape_df["floor.external_id"] == floor.external_id
    else:
        floor_selection = (shape_df["floor.floor_index"] == floor.floor_index) & (
            shape_df["floor.building.admin_id"] == floor.building.admin_id
        )  # TODO: USE Floor.compute_key instead

    shape_df = shape_df[floor_selection]

    if len(shape_df) == 0:
        # logger.warning(f"No location were found for {floor.__desc__}")

        return

    # logger.warning(shape_df.columns)

    column_selection = [
        c
        for c in shape_df.columns
        if ("." not in c)
        or ("location_type.name" == c)
        or (
            "custom_properties." in c
            and (".custom_properties" not in c)  # Only this objects custom_properties
        )
    ]

    if column_selection:
        selected = shape_df[column_selection]
    else:
        selected = shape_df

    locations_df = geopandas.GeoDataFrame(selected, geometry=geometry_column_name.value)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    process_custom_props_df(locations_df)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    empty_lines = locations_df[locations_df.is_empty]
    if not empty_lines.empty:
        logger.warning(f"Dropping {empty_lines}")

    locations_df = locations_df[~locations_df.is_empty]

    reproject_geometry_df(locations_df)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    if not len(shape_df):
        # logger.warning(f"Nothing to be added, skipping {name}")
        return

    for attr_name in BOOLEAN_LOCATION_ATTRS:
        locations_df[attr_name] = shape_df[attr_name].astype(bool)

    for attr_name in STR_LOCATION_ATTRS:
        locations_df[attr_name] = shape_df[attr_name].astype(str)

    for attr_name in FLOAT_LOCATION_ATTRS:
        locations_df[attr_name] = shape_df[attr_name].astype(float)

    for attr_name in INT_LOCATION_ATTRS:
        locations_df[attr_name] = shape_df[attr_name].astype(int)

    added_layers = add_dataframe_layer(
        qgis_instance_handle=qgis_instance_handle,
        dataframe=locations_df,
        geometry_column=geometry_column_name.value,
        name=name,
        group=floor_group,
        categorise_by_attribute="location_type.name",
        crs=solve_target_crs_authid(),
    )

    layer = None
    for a in added_layers:
        if a:
            if isinstance(a, Iterable):
                for i in a:
                    if i:
                        layer = i
                        break
                if layer:
                    break
            else:
                layer = a
                break
    else:
        # logger.warning(            f"Did not add any {geom_type} layers for {name}:{floor.__desc__}!"        )
        return

    assert (
        len(shape_df) == layer.featureCount()
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={layer.featureCount()}"

    if dropdown_widget:
        add_dropdown_widget(
            added_layers,
            "location_type.name",
            dropdown_widget,
        )

    make_field_unique(added_layers, field_name="admin_id")

    for field_name in ("name", "location_type.name", "is_searchable", "is_active"):
        make_field_not_null(added_layers, field_name=field_name)

    for field_name, field_default in {"is_searchable": True, "is_active": True}.items():
        make_field_default(
            added_layers, field_name=field_name, default_expression=f"'{field_default}'"
        )

    if False:
        for field_name in BOOLEAN_LOCATION_ATTRS:
            make_field_boolean(added_layers, field_name=field_name)

    for field_name in ("name", "location_type.name", "is_searchable", "is_active"):
        make_field_reuse_last_entered_value(added_layers, field_name=field_name)

    return added_layers


def add_floor_content_layers(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    floor: Floor,
    floor_group: Any,
    available_location_type_map_widget: Optional[Any] = None,
) -> None:
    room_layer = add_location_layer(
        location_collection=solution.rooms,
        name=BackendLocationTypeEnum.ROOM.value,
        geometry_column_name=LocationGeometryType.polygon,
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )
    set3dviewsettings(
        room_layer,
        offset=FLOOR_VERTICAL_SPACING
        + (FLOOR_HEIGHT + FLOOR_VERTICAL_SPACING) * floor.floor_index,
        extrusion=FLOOR_HEIGHT,
    )
    # set_geometry_constraints(room_layer)

    area_layer = add_location_layer(
        location_collection=solution.areas,
        name=BackendLocationTypeEnum.AREA.value,
        geometry_column_name=LocationGeometryType.polygon,
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )
    # set_geometry_constraints(area_layer)

    poi_layer = add_location_layer(
        location_collection=solution.points_of_interest,
        name=BackendLocationTypeEnum.POI.value,
        geometry_column_name=LocationGeometryType.point,
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )


if __name__ == "__main__":
    print(str(LocationGeometryType.polygon))
