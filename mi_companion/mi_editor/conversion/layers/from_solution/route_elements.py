import logging
from collections import defaultdict
from typing import Any, Optional

import geopandas
from geopandas import GeoDataFrame
from jord.qgis_utilities.fields import (
    add_dropdown_widget,
    make_field_unique,
)
from jord.qlive_utilities import add_dataframe_layer

from integration_system.model import (
    Avoid,
    Barrier,
    CollectionMixin,
    Connection,
    ConnectionCollection,
    Door,
    DoorCollection,
    EntryPoint,
    Graph,
    Obstacle,
    Prefer,
    RouteElementItem,
    Solution,
)
from mi_companion import (
    AVOIDS_DESCRIPTOR,
    BARRIERS_DESCRIPTOR,
    CONNECTORS_DESCRIPTOR,
    DOORS_DESCRIPTOR,
    ENTRY_POINTS_DESCRIPTOR,
    MAKE_FLOOR_WISE_LAYERS,
    OBSTACLES_DESCRIPTOR,
    PREFERS_DESCRIPTOR,
)
from mi_companion.constants import (
    GDS_EPSG_NUMBER,
    INSERT_INDEX,
    MI_EPSG_NUMBER,
)
from mi_companion.mi_editor.conversion.layers.from_solution.custom_props import to_df
from mi_companion.mi_editor.conversion.projection import (
    reproject_geometry_df,
    should_reproject,
)

logger = logging.getLogger(__name__)

__all__ = ["add_route_element_layers"]


def add_connection_layers(
    *,
    dropdown_widget: Optional[Any] = None,
    graph_group: Any,
    qgis_instance_handle: Any,
    graph: Graph,
    connections: ConnectionCollection,
) -> None:
    connectors = {}
    for c in connections:
        for connector_key, connector in c.connectors.items():
            connectors[connector.admin_id] = {
                "floor_index": connector.floor_index,
                "point": connector.point,
                "connection_id": c.connection_id,
                "connection_type": c.connection_type.value,
                "graph.graph_id": c.graph.graph_id,
            }

    if len(connectors) == 0:
        return

    df = (
        GeoDataFrame.from_dict(connectors, orient="index")
        .reset_index(names="external_id")
        .set_geometry("point")
    )  # Pandas pain....

    df["floor_index"] = df["floor_index"].astype(str)

    if MAKE_FLOOR_WISE_LAYERS:
        doors_group = graph_group.insertGroup(INSERT_INDEX, CONNECTORS_DESCRIPTOR)

        if not df.empty:
            floor_indices = df["floor_index"].unique()
            for floor_index in floor_indices:
                sub_df = df[
                    (df["floor_index"] == floor_index)
                    & (df["graph.graph_id"] == graph.graph_id)
                ]
                door_df = geopandas.GeoDataFrame(
                    sub_df[[c for c in sub_df.columns if ("." not in c)]],
                    geometry="point",
                )

                # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

                empty_lines = df[df.is_empty]
                if not empty_lines.empty:
                    logger.warning(f"Dropping {empty_lines}")

                df = df[~df.is_empty]

                reproject_geometry_df(door_df)

                door_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=door_df,
                    geometry_column="point",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
                )

                # if dropdown_widget:
                #  add_dropdown_widget(door_layer, "door_type", dropdown_widget)

                make_field_unique(door_layer, field_name="external_id")
    else:
        empty_lines = df[df.is_empty]
        if not empty_lines.empty:
            logger.warning(f"Dropping {empty_lines}")

        df = df[~df.is_empty]

        reproject_geometry_df(df)

        connectors_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=df,
            geometry_column="point",
            name=CONNECTORS_DESCRIPTOR,
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
        )

        make_field_unique(connectors_layer, field_name="external_id")


def add_route_element_layers(
    *,
    qgis_instance_handle: Any,
    graph_group: Any,
    graph: Graph,
    dropdown_widget: Optional[Any] = None,
    solution: Solution,
) -> None:
    split_levels_into_individual_groups: bool = False
    if split_levels_into_individual_groups:
        route_element_collections = {
            Door: solution.doors,
            Avoid: solution.avoids,
            Prefer: solution.prefers,
            Barrier: solution.barriers,
            EntryPoint: solution.entry_points,
            Obstacle: solution.obstacles,
            Connection: solution.connections,
        }
        unique_levels = defaultdict(dict)
        for type_, res in route_element_collections:
            for re in res:
                re: RouteElementItem
                if isinstance(re, RouteElementItem):
                    unique_levels[re.floor_index][type_] = re
                elif isinstance(re, Connection):
                    for key, connector in re.connectors.items():
                        unique_levels[connector.floor_index][type_][re.connection_id][
                            re.connection_type
                        ] = re
                else:
                    raise NotImplementedError(f"{re} is not supported")

        unique_levels = sorted(list(unique_levels))
        for level in unique_levels:
            ...  # TODO: NOT IMPLEMENTED YET

    else:
        add_linestring_route_element_layers(
            dropdown_widget=dropdown_widget,
            graph=graph,
            graph_group=graph_group,
            qgis_instance_handle=qgis_instance_handle,
            doors=solution.doors,
        )

        for desc, col in {
            AVOIDS_DESCRIPTOR: solution.avoids,
            PREFERS_DESCRIPTOR: solution.prefers,
            BARRIERS_DESCRIPTOR: solution.barriers,
            ENTRY_POINTS_DESCRIPTOR: solution.entry_points,
        }.items():
            add_point_route_element_layers(
                graph=graph,
                graph_group=graph_group,
                qgis_instance_handle=qgis_instance_handle,
                route_element_collection=col,
                layer_descriptor=desc,
            )

        if False:
            add_polygon_route_element_layers(
                graph=graph,
                graph_group=graph_group,
                qgis_instance_handle=qgis_instance_handle,
                route_element_collection=solution.obstacles,
                layer_descriptor=OBSTACLES_DESCRIPTOR,
            )

        add_connection_layers(
            dropdown_widget=dropdown_widget,
            graph_group=graph_group,
            qgis_instance_handle=qgis_instance_handle,
            connections=solution.connections,
            graph=graph,
        )


def add_linestring_route_element_layers(
    *,
    dropdown_widget: Optional[Any] = None,
    graph: Graph,
    graph_group: Any,
    qgis_instance_handle: Any,
    doors: DoorCollection,
) -> None:
    doors_name = f"{DOORS_DESCRIPTOR}"

    if len(doors) == 0:
        return

    df = to_df(doors)

    if "floor_index" not in df:
        logger.warning(
            f"No floor index found for {doors_name}, {df.columns}, {len(df)}"
        )
        return

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

                empty_lines = door_df[door_df.is_empty]
                if not empty_lines.empty:
                    logger.warning(f"Dropping {empty_lines}")

                door_df = door_df[~door_df.is_empty]

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

                make_field_unique(door_layer, field_name="external_id")
    else:
        door_df = geopandas.GeoDataFrame(
            df[[c for c in df.columns if ("." not in c)]],
            geometry="linestring",
        )

        # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

        empty_lines = door_df[door_df.is_empty]
        if not empty_lines.empty:
            logger.warning(f"Dropping {empty_lines}")

        door_df = door_df[~door_df.is_empty]

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

        make_field_unique(door_layer, field_name="external_id")


def add_point_route_element_layers(
    *,
    dropdown_widget: Optional[Any] = None,
    graph: Graph,
    graph_group: Any,
    qgis_instance_handle: Any,
    layer_descriptor: str,
    route_element_collection: CollectionMixin,
) -> None:
    doors_name = layer_descriptor

    if len(route_element_collection) == 0:
        return

    df = to_df(route_element_collection)

    if "floor_index" not in df:
        logger.warning(
            f"No floor index found for {doors_name}, {df.columns}, {len(df)}"
        )
        return

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
                    geometry="point",
                )

                # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

                empty_lines = door_df[door_df.is_empty]
                if not empty_lines.empty:
                    logger.warning(f"Dropping {empty_lines}")

                door_df = door_df[~door_df.is_empty]

                reproject_geometry_df(door_df)

                door_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=door_df,
                    geometry_column="point",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
                )

                if dropdown_widget:
                    add_dropdown_widget(door_layer, "door_type", dropdown_widget)

                make_field_unique(door_layer, field_name="external_id")
    else:
        door_df = geopandas.GeoDataFrame(
            df[[c for c in df.columns if ("." not in c)]],
            geometry="point",
        )

        # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

        empty_lines = door_df[door_df.is_empty]
        if not empty_lines.empty:
            logger.warning(f"Dropping {empty_lines}")

        door_df = door_df[~door_df.is_empty]

        reproject_geometry_df(door_df)

        door_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=door_df,
            geometry_column="point",
            name=f"{doors_name}",
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
        )

        if dropdown_widget:
            add_dropdown_widget(door_layer, "door_type", dropdown_widget)

        make_field_unique(door_layer, field_name="external_id")


def add_polygon_route_element_layers(
    *,
    dropdown_widget: Optional[Any] = None,
    graph: Graph,
    graph_group: Any,
    qgis_instance_handle: Any,
    doors: DoorCollection,
) -> None:
    doors_name = f"{OBSTACLES_DESCRIPTOR}"
    df = to_df(doors)

    if "floor_index" not in df:
        logger.warning(f"No floor index found for {doors_name}")
        return

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
                    geometry="polygon",
                )

                # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

                empty_lines = door_df[door_df.is_empty]
                if not empty_lines.empty:
                    logger.warning(f"Dropping {empty_lines}")

                door_df = door_df[~door_df.is_empty]

                reproject_geometry_df(door_df)

                door_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=door_df,
                    geometry_column="polygon",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
                )

                if dropdown_widget:
                    add_dropdown_widget(door_layer, "door_type", dropdown_widget)

                make_field_unique(door_layer, field_name="external_id")
    else:
        door_df = geopandas.GeoDataFrame(
            df[[c for c in df.columns if ("." not in c)]],
            geometry="polygon",
        )

        # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

        empty_lines = door_df[door_df.is_empty]
        if not empty_lines.empty:
            logger.warning(f"Dropping {empty_lines}")

        door_df = door_df[~door_df.is_empty]

        reproject_geometry_df(door_df)

        door_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=door_df,
            geometry_column="polygon",
            name=f"{doors_name}",
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
        )

        if dropdown_widget:
            add_dropdown_widget(door_layer, "door_type", dropdown_widget)

        make_field_unique(door_layer, field_name="external_id")
