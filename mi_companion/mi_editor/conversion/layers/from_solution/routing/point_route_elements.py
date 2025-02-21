import logging
from typing import Any, Optional

import geopandas
from jord.qgis_utilities.fields import (
    add_dropdown_widget,
    add_dropdown_widget,
    make_field_not_null,
    make_field_not_null,
    make_field_unique,
    make_field_unique,
)
from jord.qlive_utilities import add_dataframe_layer, add_dataframe_layer

from integration_system.model import CollectionMixin, Graph
from mi_companion import INSERT_INDEX, MAKE_FLOOR_WISE_LAYERS
from mi_companion.mi_editor.conversion.layers.from_solution.custom_props import to_df
from mi_companion.mi_editor.conversion.projection import (
    reproject_geometry_df,
    solve_target_crs_authid,
)

logger = logging.getLogger(__name__)

__all__ = ["add_point_route_element_layers"]


def add_point_route_element_layers(
    *,
    dropdown_widget: Optional[Any] = None,
    route_element_type_column: str = None,
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

                point_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=door_df,
                    geometry_column="point",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=solve_target_crs_authid(),
                )

                for field_name in ("floor_index",):
                    make_field_not_null(point_layer, field_name=field_name)

                make_field_unique(point_layer, field_name="admin_id")

                if (
                    dropdown_widget is not None
                    and route_element_type_column is not None
                ):
                    add_dropdown_widget(
                        point_layer, route_element_type_column, dropdown_widget
                    )
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

        point_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=door_df,
            geometry_column="point",
            name=f"{doors_name}",
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=solve_target_crs_authid(),
        )

        for field_name in ("floor_index",):
            make_field_not_null(point_layer, field_name=field_name)

        make_field_unique(point_layer, field_name="admin_id")

        if dropdown_widget is not None and route_element_type_column is not None:
            add_dropdown_widget(point_layer, route_element_type_column, dropdown_widget)
