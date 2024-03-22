import dataclasses
import logging
from typing import Optional, Mapping

import geopandas
from jord.qlive_utilities import add_dataframe_layer
from pandas import DataFrame, json_normalize

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

import integration_system.model
from integration_system.model.mixins import CollectionMixin
from mi_companion.configuration.constants import (
    ADD_GRAPH,
    MAKE_DOOR_TYPE_DROPDOWN,
)

__all__ = ["add_inventory_layers"]


logger = logging.getLogger(__name__)


def to_df(coll_mix: CollectionMixin) -> DataFrame:
    # noinspection PyTypeChecker
    return json_normalize(dataclasses.asdict(obj) for obj in coll_mix)


def add_inventory_layers(
    *,
    qgis_instance_handle,
    solution,
    floor,
    floor_group,
    venue,
    available_location_type_map: Optional[Mapping[str, str]] = None,
) -> None:
    rooms = to_df(solution.rooms)
    if not rooms.empty:
        rooms = rooms[rooms["floor.external_id"] == floor.external_id]
        rooms_df = geopandas.GeoDataFrame(
            rooms[
                [
                    c
                    for c in rooms.columns
                    if ("." not in c) or ("location_type.name" == c)
                ]
            ],
            geometry="polygon",
        )

        added_layers = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=rooms_df,
            geometry_column="polygon",
            name="rooms",
            group=floor_group,
            categorise_by_attribute="location_type.name",
        )

        if available_location_type_map:
            # https://gis.stackexchange.com/questions/470963/setting-dropdown-on-feature-attribute-form-using-plugin

            for layers_inner in added_layers:
                if layers_inner:
                    for layer in layers_inner:
                        if layer:
                            layer.setEditorWidgetSetup(
                                layer.fields().indexFromName("location_type.name"),
                                QgsEditorWidgetSetup(
                                    "ValueMap", {"map": available_location_type_map}
                                ),
                            )

    if ADD_GRAPH:
        doors = to_df(solution.doors)
        if not doors.empty:
            doors = doors[
                (doors["floor_index"] == floor.floor_index)
                & (doors["graph.graph_id"] == venue.graph.graph_id)
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

            if MAKE_DOOR_TYPE_DROPDOWN:
                available_door_type_map = sorted(
                    {l.name: l.name for l in integration_system.model.DoorType}
                )

                for layers_inner in door_layer:
                    if layers_inner:
                        for layer in layers_inner:
                            if layer:
                                layer.setEditorWidgetSetup(
                                    layer.fields().indexFromName("door_type"),
                                    QgsEditorWidgetSetup(
                                        "ValueMap", {"map": available_door_type_map}
                                    ),
                                )

    areas = to_df(solution.areas)
    if not areas.empty:
        areas = areas[areas["floor.external_id"] == floor.external_id]
        areas_df = geopandas.GeoDataFrame(
            areas[
                [
                    c
                    for c in areas.columns
                    if ("." not in c) or ("location_type.name" == c)
                ]
            ],
            geometry="polygon",
        )

        added_layers = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=areas_df,
            geometry_column="polygon",
            name="areas",
            group=floor_group,
            categorise_by_attribute="location_type.name",
        )

        if available_location_type_map:
            # https://gis.stackexchange.com/questions/470963/setting-dropdown-on-feature-attribute-form-using-plugin

            for layers_inner in added_layers:
                if layers_inner:
                    for layer in layers_inner:
                        if layer:
                            layer.setEditorWidgetSetup(
                                layer.fields().indexFromName("location_type.name"),
                                QgsEditorWidgetSetup(
                                    "ValueMap", {"map": available_location_type_map}
                                ),
                            )

    pois = to_df(solution.points_of_interest)
    if not pois.empty:
        pois = pois[pois["floor.external_id"] == floor.external_id]
        poi_df = geopandas.GeoDataFrame(
            pois[
                [
                    c
                    for c in pois.columns
                    if ("." not in c) or ("location_type.name" == c)
                ]
            ],
            geometry="point",
        )

        added_layers = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=poi_df,
            geometry_column="point",
            name="pois",
            group=floor_group,
            categorise_by_attribute="location_type.name",
        )

        if available_location_type_map:
            # https://gis.stackexchange.com/questions/470963/setting-dropdown-on-feature-attribute-form-using-plugin

            for layers_inner in added_layers:
                if layers_inner:
                    for layer in layers_inner:
                        if layer:
                            layer.setEditorWidgetSetup(
                                layer.fields().indexFromName("location_type.name"),
                                QgsEditorWidgetSetup(
                                    "ValueMap", {"map": available_location_type_map}
                                ),
                            )
