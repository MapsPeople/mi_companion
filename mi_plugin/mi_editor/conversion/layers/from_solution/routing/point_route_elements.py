import logging
from typing import Any, List, Optional

import geopandas

from jord.qgis_utilities import (
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
    set_field_widget,
)
from jord.qlive_utilities import add_dataframe_layer
from mi_plugin import INSERT_INDEX, MAKE_FLOOR_WISE_LAYERS
from mi_plugin.mi_editor.conversion.projection import (
    reproject_geometry_df_qgis,
    solve_target_crs_authid,
)
from sync_module.model import CollectionMixin, Graph
from sync_module.pandas_utilities import locations_to_df

__all__ = ["add_point_route_element_layers"]

_logger = logging.getLogger(__name__)


def add_point_route_element_layers(
    *,
    dropdown_widget: Optional[Any] = None,
    route_element_type_column: str = None,
    graph: Graph,
    graph_group: Any,
    qgis_instance_handle: Any,
    layer_descriptor: str,
    route_element_collection: CollectionMixin,
) -> List[Any]:
    layer_name = layer_descriptor

    if len(route_element_collection) == 0:
        return []

    df = locations_to_df(route_element_collection)

    if "floor_index" not in df:
        _logger.warning(
            f"No floor index found for {layer_name}, {df.columns}, {len(df)}"
        )
        return []

    df["floor_index"] = df["floor_index"].astype(str)

    if "wait_time" in df:
        df["wait_time"] = df["wait_time"].astype("Int64")

    if "bearing" in df:
        df["bearing"] = df["bearing"].astype(float)
    # TODO: opening_hours is missing
    if "fields" in df:  # TODO: Is this right?
        df.pop("fields")

    added_layers = []

    if MAKE_FLOOR_WISE_LAYERS:
        doors_group = graph_group.insertGroup(INSERT_INDEX, layer_name)

        if not df.empty:
            floor_indices = df["floor_index"].unique()
            for floor_index in floor_indices:
                sub_df = df[
                    (df["floor_index"] == floor_index)
                    & (df["graph.graph_id"] == graph.graph_id)
                ]
                route_element_df = geopandas.GeoDataFrame(
                    sub_df[
                        [
                            c
                            for c in sub_df.columns
                            if ("." not in c) or ("fields." in c)
                        ]
                    ],
                    geometry="point",
                )

                # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

                empty_lines = route_element_df[route_element_df.is_empty]
                if not empty_lines.empty:
                    _logger.warning(f"Dropping {empty_lines}")

                route_element_df = route_element_df[~route_element_df.is_empty]

                reproject_geometry_df_qgis(route_element_df)

                point_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=route_element_df,
                    geometry_column="point",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=solve_target_crs_authid(),
                )

                added_layers.append(point_layer)

                for field_name in ("floor_index",):
                    make_field_not_null(point_layer, field_name=field_name)
                    make_field_reuse_last_entered_value(
                        point_layer, field_name=field_name
                    )

                make_field_unique(point_layer, field_name="admin_id")

                for field_name in ("wait_time",):
                    ...

                for field_name in ("bearing",):
                    ...

                if (
                    dropdown_widget is not None
                    and route_element_type_column is not None
                ):
                    set_field_widget(
                        point_layer, route_element_type_column, dropdown_widget
                    )
    else:
        route_element_df = geopandas.GeoDataFrame(
            df[[c for c in df.columns if ("." not in c)]],
            geometry="point",
        )

        # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

        empty_lines = route_element_df[route_element_df.is_empty]
        if not empty_lines.empty:
            _logger.warning(f"Dropping {empty_lines}")

        route_element_df = route_element_df[~route_element_df.is_empty]

        reproject_geometry_df_qgis(route_element_df)

        point_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=route_element_df,
            geometry_column="point",
            name=f"{layer_name}",
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=solve_target_crs_authid(),
        )

        added_layers.append(point_layer)

        for field_name in ("floor_index",):
            make_field_not_null(point_layer, field_name=field_name)
            make_field_reuse_last_entered_value(point_layer, field_name=field_name)

        for field_name in ("wait_time",):
            ...

        for field_name in ("bearing",):
            ...

        make_field_unique(point_layer, field_name="admin_id")

        if dropdown_widget is not None and route_element_type_column is not None:
            set_field_widget(point_layer, route_element_type_column, dropdown_widget)

    return added_layers
