import logging
from typing import Any, Iterable, List, Optional

import geopandas
from integration_system.model import (
    CollectionMixin,
    Floor,
    Solution,
)
from jord.qlive_utilities import add_dataframe_layer

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

__all__ = ["add_floor_content_layers"]

from .custom_props import process_custom_props_df, to_df

from ..type_enums import LocationTypeEnum
from .fields import add_dropdown_widget, make_field_unique
from ...projection import (
    reproject_geometry_df,
    MI_EPSG_NUMBER,
    should_reproject,
    GDS_EPSG_NUMBER,
)

logger = logging.getLogger(__name__)

USE_EXTERNAL_ID_FLOOR_SELECTION = False


def add_location_layer(
    collection_: CollectionMixin,
    name: str,
    geom_type: str,
    *,
    qgis_instance_handle: Any,
    floor_group: Any,
    floor: Floor,
    dropdown_widget: Optional[Any] = None,
) -> Optional[List[Any]]:  # QgsVectorLayer
    shape_df = to_df(collection_)

    assert len(collection_) == len(shape_df)
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

    locations_df = geopandas.GeoDataFrame(selected, geometry=geom_type)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    process_custom_props_df(locations_df)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    reproject_geometry_df(locations_df)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    if not len(shape_df):
        # logger.warning(f"Nothing to be added, skipping {name}")
        return

    added_layers = add_dataframe_layer(
        qgis_instance_handle=qgis_instance_handle,
        dataframe=locations_df,
        geometry_column=geom_type,
        name=name,
        group=floor_group,
        categorise_by_attribute="location_type.name",
        crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
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

    make_field_unique(added_layers)

    return added_layers


def add_floor_content_layers(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    floor: Floor,
    floor_group: Any,
    available_location_type_map_widget: Optional[Any] = None,
) -> None:
    add_location_layer(
        solution.points_of_interest,
        LocationTypeEnum.POI.value,
        "point",
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )

    add_location_layer(
        solution.rooms,
        LocationTypeEnum.ROOM.value,
        "polygon",
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )

    add_location_layer(
        solution.areas,
        LocationTypeEnum.AREA.value,
        "polygon",
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )
