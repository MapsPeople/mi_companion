import dataclasses
import logging
from typing import Optional, Any, Iterable, List

import geopandas
from jord.qlive_utilities import add_dataframe_layer
from pandas import DataFrame, json_normalize

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

from integration_system.mi.manager_model import MIVenue, MIFloor
from integration_system.model import Solution
from integration_system.model.mixins import CollectionMixin
from mi_companion.configuration.constants import (
    ADD_GRAPH,
)

__all__ = ["add_inventory_layers"]

from mi_companion.mi_editor.conversion.layers.type_enums import InventoryTypeEnum

logger = logging.getLogger(__name__)


def to_df(coll_mix: CollectionMixin) -> DataFrame:
    # noinspection PyTypeChecker
    return json_normalize(dataclasses.asdict(obj) for obj in coll_mix)


def add_dropdown_widget(layer, field_name: str, widget) -> None:
    # https://gis.stackexchange.com/questions/470963/setting-dropdown-on-feature-attribute-form-using-plugin
    for layers_inner in layer:
        if layers_inner:
            if isinstance(layers_inner, Iterable):
                for layer in layers_inner:
                    if layer:
                        layer.setEditorWidgetSetup(
                            layer.fields().indexFromName(field_name),
                            widget,
                        )
            else:
                layers_inner.setEditorWidgetSetup(
                    layers_inner.fields().indexFromName(field_name),
                    widget,
                )


def add_inventory_layer(
    collection_: CollectionMixin,
    name: str,
    geom_type: str,
    *,
    qgis_instance_handle,
    floor_group,
    floor,
    dropdown_widget
) -> List:
    shape_df = to_df(collection_)
    if not shape_df.empty:
        shape_df = shape_df[shape_df["floor.external_id"] == floor.external_id]
        rooms_df = geopandas.GeoDataFrame(
            shape_df[
                [
                    c
                    for c in shape_df.columns
                    if ("." not in c)
                    or ("location_type.name" == c)
                    or (
                        "custom_properties" in c
                        and (
                            ".custom_properties" not in c
                        )  # Only this objects custom_properties
                    )
                ]
            ],
            geometry=geom_type,
        )

        added_layers = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=rooms_df,
            geometry_column=geom_type,
            name=name,
            group=floor_group,
            categorise_by_attribute="location_type.name",
        )

        if dropdown_widget:
            add_dropdown_widget(
                added_layers,
                "location_type.name",
                dropdown_widget,
            )

        return added_layers


def add_door_layer(
    collection_: CollectionMixin,
    *,
    qgis_instance_handle,
    floor_group,
    floor,
    graph,
    dropdown_widget
):
    doors = to_df(collection_)
    if not doors.empty:
        doors = doors[
            (doors["floor_index"] == floor.floor_index)
            & (doors["graph.graph_id"] == graph.graph_id)
        ]
        door_df = geopandas.GeoDataFrame(
            doors[[c for c in doors.columns if ("." not in c)]],
            geometry="linestring",
        )

        door_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=door_df,
            geometry_column="linestring",
            name="doors",
            categorise_by_attribute="door_type",
            group=floor_group,
        )

        if dropdown_widget:
            add_dropdown_widget(door_layer, "door_type", dropdown_widget)


def add_inventory_layers(
    *,
    qgis_instance_handle,
    solution: Solution,
    floor: MIFloor,
    floor_group,
    venue: MIVenue,
    available_location_type_map_widget: Optional[Any] = None,
    door_type_dropdown_widget: Optional[Any] = None
) -> None:
    add_inventory_layer(
        solution.rooms,
        InventoryTypeEnum.room.value,
        "polygon",
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )

    if ADD_GRAPH:
        add_door_layer(
            solution.doors,
            graph=venue.graph,
            qgis_instance_handle=qgis_instance_handle,
            floor_group=floor_group,
            floor=floor,
            dropdown_widget=door_type_dropdown_widget,
        )

    add_inventory_layer(
        solution.areas,
        InventoryTypeEnum.area.value,
        "polygon",
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )

    add_inventory_layer(
        solution.points_of_interest,
        InventoryTypeEnum.poi.value,
        "point",
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        dropdown_widget=available_location_type_map_widget,
    )
