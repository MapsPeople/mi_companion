import copy
import dataclasses
import logging
from typing import Any, List, Optional

import geopandas
from jord.qlive_utilities import add_dataframe_layer
from pandas import DataFrame, json_normalize

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

from integration_system.mi import MIFloor, MIVenue
from integration_system.mixins import CollectionMixin
from integration_system.model import Solution
from mi_companion.configuration.constants import (
    REAL_NONE_JSON_VALUE,
)

__all__ = ["add_floor_content_layers"]

from mi_companion.configuration.options import read_bool_setting

from .custom_props import process_custom_props_df

from mi_companion.mi_editor.conversion.layers.type_enums import LocationTypeEnum
from .fields import add_dropdown_widget, make_field_unique
from ...projection import (
    reproject_geometry_df,
    MI_EPSG_NUMBER,
    should_reproject,
    GDS_EPSG_NUMBER,
)

logger = logging.getLogger(__name__)


def to_df(coll_mix: CollectionMixin) -> DataFrame:
    # noinspection PyTypeChecker
    cs = []
    for c in coll_mix:
        if hasattr(c, "custom_properties"):
            cps = getattr(c, "custom_properties")
            if cps is not None:
                for language, translations in copy.deepcopy(cps).items():
                    for cp, cpv in translations.items():
                        if cpv is None:
                            cps[language][cp] = REAL_NONE_JSON_VALUE
                setattr(c, "custom_properties", cps)
        cs.append(dataclasses.asdict(c))
    return json_normalize(cs)


def add_location_layer(
    collection_: CollectionMixin,
    name: str,
    geom_type: str,
    *,
    qgis_instance_handle,
    floor_group,
    floor,
    dropdown_widget,
) -> Optional[List[Any]]:  # QgsVectorLayer
    shape_df = to_df(collection_)
    if not shape_df.empty:
        shape_df = shape_df[shape_df["floor.external_id"] == floor.external_id]

        locations_df = geopandas.GeoDataFrame(
            shape_df[
                [
                    c
                    for c in shape_df.columns
                    if ("." not in c)
                    or ("location_type.name" == c)
                    or (
                        "custom_properties." in c
                        and (
                            ".custom_properties" not in c
                        )  # Only this objects custom_properties
                    )
                ]
            ],
            geometry=geom_type,
        )
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

        added_layers = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=locations_df,
            geometry_column=geom_type,
            name=name,
            group=floor_group,
            categorise_by_attribute="location_type.name",
            crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
        )

        for a in added_layers:
            if a:
                layer = next(iter(a))
                break
        else:
            logger.error(f"Did not add any layers!")
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


def add_door_layer(
    collection_: CollectionMixin,
    *,
    qgis_instance_handle,
    floor_group,
    floor,
    graph,
    dropdown_widget,
):
    df = to_df(collection_)
    if not df.empty:
        df = df[
            (df["floor_index"] == floor.floor_index)
            & (df["graph.graph_id"] == graph.graph_id)
        ]
        door_df = geopandas.GeoDataFrame(
            df[[c for c in df.columns if ("." not in c)]],
            geometry="linestring",
        )

        # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

        reproject_geometry_df(door_df)

        door_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=door_df,
            geometry_column="linestring",
            name="doors",
            categorise_by_attribute="door_type",
            group=floor_group,
            crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
        )

        if dropdown_widget:
            add_dropdown_widget(door_layer, "door_type", dropdown_widget)

        make_field_unique(door_layer)


def add_floor_content_layers(
    *,
    qgis_instance_handle,
    solution: Solution,
    floor: MIFloor,
    floor_group,
    venue: MIVenue,
    available_location_type_map_widget: Optional[Any] = None,
    door_type_dropdown_widget: Optional[Any] = None,
) -> None:
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

    add_location_layer(
        solution.points_of_interest,
        LocationTypeEnum.POI.value,
        "point",
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )

    if read_bool_setting("ADD_DOORS"):
        add_door_layer(
            solution.doors,
            graph=venue.graph,
            qgis_instance_handle=qgis_instance_handle,
            floor_group=floor_group,
            floor=floor,
            dropdown_widget=door_type_dropdown_widget,
        )
