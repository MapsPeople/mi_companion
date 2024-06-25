from typing import Any, Optional

import geopandas
from jord.qlive_utilities import add_dataframe_layer

from integration_system.model import DoorCollection, Graph, Solution
from mi_companion.configuration.constants import (
    CONNECTORS_DESCRIPTOR,
    DOORS_DESCRIPTOR,
    MAKE_FLOOR_WISE_LAYERS,
)
from mi_companion.mi_editor.conversion.layers.from_solution.custom_props import to_df
from mi_companion.mi_editor.conversion.layers.from_solution.fields import (
    add_dropdown_widget,
    make_field_unique,
)
from mi_companion.mi_editor.conversion.projection import (
    GDS_EPSG_NUMBER,
    INSERT_INDEX,
    MI_EPSG_NUMBER,
    reproject_geometry_df,
    should_reproject,
)


def add_connection_layers(
    dropdown_widget, graph, graph_group, qgis_instance_handle, connections
):
    connections_name = f"{graph.graph_id} {CONNECTORS_DESCRIPTOR}"
    connections_group = graph_group.insertGroup(INSERT_INDEX, connections_name)
    df = to_df(connections)
    if not df.empty:
        floor_indices = df["floor_index"].unique()
        for floor_index in floor_indices:
            sub_df = df[
                (df["floor_index"] == floor_index)
                & (df["graph.graph_id"] == graph.graph_id)
            ]
            door_df = geopandas.GeoDataFrame(
                sub_df[[c for c in sub_df.columns if ("." not in c)]],
                geometry="linestring",
            )

            # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

            reproject_geometry_df(door_df)

            door_layer = add_dataframe_layer(
                qgis_instance_handle=qgis_instance_handle,
                dataframe=door_df,
                geometry_column="linestring",
                name=f"{floor_index}",
                categorise_by_attribute="floor_index",
                group=connections_group,
                crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
            )

            if dropdown_widget:
                add_dropdown_widget(door_layer, "door_type", dropdown_widget)

            make_field_unique(door_layer)


def add_route_element_layers(
    *,
    qgis_instance_handle: Any,
    graph_group: Any,
    graph: Graph,
    dropdown_widget: Optional[Any] = None,
    solution: Solution,
) -> None:
    add_door_layers(
        dropdown_widget=dropdown_widget,
        graph=graph,
        graph_group=graph_group,
        qgis_instance_handle=qgis_instance_handle,
        doors=solution.doors,
    )
    # add_connection_layers(        dropdown_widget=dropdown_widget,        graph=graph,        graph_group=graph_group,        qgis_instance_handle=qgis_instance_handle,        connections=solution.connections,    )


def add_door_layers(
    *,
    dropdown_widget: Any,
    graph: Graph,
    graph_group: Any,
    qgis_instance_handle: Any,
    doors: DoorCollection,
) -> None:
    doors_name = f"{DOORS_DESCRIPTOR}"
    df = to_df(doors)
    df["floor_index"] = df["floor_index"].astype(str)

    if MAKE_FLOOR_WISE_LAYERS:
        doors_group = graph_group.insertGroup(INSERT_INDEX, doors_name)

        if not df.empty:
            floor_indices = df["floor_index"].unique()
            for floor_index in floor_indices:
                sub_df = df[
                    (df["floor_index"] == floor_index)
                    & (df["graph.graph_id"] == graph.graph_id)
                ]
                door_df = geopandas.GeoDataFrame(
                    sub_df[[c for c in sub_df.columns if ("." not in c)]],
                    geometry="linestring",
                )

                # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

                reproject_geometry_df(door_df)

                door_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=door_df,
                    geometry_column="linestring",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
                )

                if dropdown_widget:
                    add_dropdown_widget(door_layer, "door_type", dropdown_widget)

                make_field_unique(door_layer)
    else:
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
            name=f"{doors_name}",
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
        )

        if dropdown_widget:
            add_dropdown_widget(door_layer, "door_type", dropdown_widget)

        make_field_unique(door_layer)
