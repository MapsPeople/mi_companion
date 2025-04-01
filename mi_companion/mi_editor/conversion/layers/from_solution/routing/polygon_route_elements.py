import logging
from typing import Any, List, Optional

import geopandas
from jord.qgis_utilities.fields import (
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
    set_field_widget,
)
from jord.qlive_utilities import add_dataframe_layer

from integration_system.model import CollectionMixin, Graph
from mi_companion import INSERT_INDEX, MAKE_FLOOR_WISE_LAYERS
from mi_companion.mi_editor.conversion.layers.from_solution.location import (
    locations_to_df,
)
from mi_companion.mi_editor.conversion.projection import (
    reproject_geometry_df,
    solve_target_crs_authid,
)

logger = logging.getLogger(__name__)

__all__ = ["add_polygon_route_element_layers"]


def add_polygon_route_element_layers(
    *,
    graph: Graph,
    graph_group: Any,
    qgis_instance_handle: Any,
    route_element_collection: CollectionMixin,
    layer_name: str,
    route_element_type_column: Optional[str] = None,
    dropdown_widget: Optional[Any] = None,
) -> Optional[List[Any]]:
    df = locations_to_df(route_element_collection)

    added_layers = []

    if "floor_index" not in df:
        logger.warning(f"No floor index found for {layer_name}")
        return None

    df["floor_index"] = df["floor_index"].astype(str)

    if MAKE_FLOOR_WISE_LAYERS:
        doors_group = graph_group.insertGroup(INSERT_INDEX, layer_name)

        if not df.empty:
            floor_indices = df["floor_index"].unique()
            for floor_index in floor_indices:
                sub_df = df[
                    (df["floor_index"] == floor_index)
                    & (df["graph.graph_id"] == graph.graph_id)
                ]
                obstacle_df = geopandas.GeoDataFrame(
                    sub_df[[c for c in sub_df.columns if ("." not in c)]],
                    geometry="polygon",
                )

                # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

                empty_lines = obstacle_df[obstacle_df.is_empty]
                if not empty_lines.empty:
                    logger.warning(f"Dropping {empty_lines}")

                obstacle_df = obstacle_df[~obstacle_df.is_empty]

                reproject_geometry_df(obstacle_df)

                obstacle_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=obstacle_df,
                    geometry_column="polygon",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=solve_target_crs_authid(),
                )

                added_layers.append(obstacle_layer)

                for field_name in ("floor_index",):
                    make_field_not_null(obstacle_layer, field_name=field_name)

                make_field_unique(obstacle_layer, field_name="admin_id")

                if (
                    dropdown_widget is not None
                    and route_element_type_column is not None
                ):
                    set_field_widget(
                        obstacle_layer, route_element_type_column, dropdown_widget
                    )

    else:
        obstacle_df = geopandas.GeoDataFrame(
            df[[c for c in df.columns if ("." not in c)]],
            geometry="polygon",
        )

        # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

        empty_lines = obstacle_df[obstacle_df.is_empty]
        if not empty_lines.empty:
            logger.warning(f"Dropping {empty_lines}")

        obstacle_df = obstacle_df[~obstacle_df.is_empty]

        reproject_geometry_df(obstacle_df)

        obstacle_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=obstacle_df,
            geometry_column="polygon",
            name=f"{layer_name}",
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=solve_target_crs_authid(),
        )

        added_layers.append(obstacle_layer)

        for field_name in ("floor_index",):
            make_field_not_null(obstacle_layer, field_name=field_name)
            make_field_reuse_last_entered_value(obstacle_layer, field_name)

        make_field_unique(obstacle_layer, field_name="admin_id")

        if dropdown_widget is not None and route_element_type_column is not None:
            set_field_widget(obstacle_layer, route_element_type_column, dropdown_widget)

    return added_layers
