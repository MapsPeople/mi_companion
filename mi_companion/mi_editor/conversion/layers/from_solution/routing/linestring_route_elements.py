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
from mi_companion import INSERT_INDEX, MAKE_FLOOR_WISE_LAYERS
from mi_companion.layer_descriptors import DOORS_GROUP_DESCRIPTOR
from mi_companion.mi_editor.conversion.projection import (
    reproject_geometry_df_qgis,
    solve_target_crs_authid,
)
from sync_module.model import DoorCollection, Graph
from sync_module.pandas_utilities import locations_to_df

logger = logging.getLogger(__name__)

__all__ = ["add_linestring_route_element_layers"]


def add_linestring_route_element_layers(
    *,
    dropdown_widget: Optional[Any] = None,
    route_element_type_column: Optional[str] = "door_type",
    graph: Graph,
    graph_group: Any,
    qgis_instance_handle: Any,
    doors: DoorCollection,
) -> List[Any]:
    doors_name = f"{DOORS_GROUP_DESCRIPTOR}"

    added_layers = []

    if len(doors) == 0:
        return []

    df = locations_to_df(doors)

    if "floor_index" not in df:
        logger.warning(
            f"No floor index found for {doors_name}, {df.columns}, {len(df)}"
        )
        return []

    df["floor_index"] = df["floor_index"].astype(str)

    if "fields" in df:  # TODO: Is this right?
        df.pop("fields")

    if MAKE_FLOOR_WISE_LAYERS:
        doors_group = graph_group.insertGroup(INSERT_INDEX, doors_name)

        if not df.empty:
            floor_indices = df["floor_index"].unique()
            for floor_index in floor_indices:
                sub_df = df[
                    (df["floor_index"] == floor_index)
                    & (df["graph.graph_id"] == graph.graph_id)
                ]

                linestring_df = geopandas.GeoDataFrame(
                    sub_df[
                        [
                            c
                            for c in sub_df.columns
                            if ("." not in c) or ("fields." in c)
                        ]
                    ],
                    geometry="linestring",
                )

                empty_lines = linestring_df[linestring_df.is_empty]
                if not empty_lines.empty:
                    logger.warning(f"Dropping {empty_lines}")

                linestring_df = linestring_df[~linestring_df.is_empty]

                # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

                reproject_geometry_df_qgis(linestring_df)

                linestring_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=linestring_df,
                    geometry_column="linestring",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=solve_target_crs_authid(),
                )

                added_layers.append(linestring_layer)

                for field_name in ("floor_index",):
                    make_field_not_null(linestring_layer, field_name=field_name)
                    make_field_reuse_last_entered_value(linestring_layer, field_name)

                make_field_unique(linestring_layer, field_name="admin_id")

                if dropdown_widget:
                    set_field_widget(
                        linestring_layer, route_element_type_column, dropdown_widget
                    )

    else:
        linestring_df = geopandas.GeoDataFrame(
            df[[c for c in df.columns if ("." not in c)]],
            geometry="linestring",
        )

        # door_df["door_type"] = door_df["door_type"].apply(lambda x: x.name, axis=1)

        empty_lines = linestring_df[linestring_df.is_empty]
        if not empty_lines.empty:
            logger.warning(f"Dropping {empty_lines}")

        linestring_df = linestring_df[~linestring_df.is_empty]

        reproject_geometry_df_qgis(linestring_df)

        linestring_layer = add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=linestring_df,
            geometry_column="linestring",
            name=f"{doors_name}",
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=solve_target_crs_authid(),
        )

        for field_name in ("floor_index",):
            make_field_not_null(linestring_layer, field_name=field_name)
            make_field_reuse_last_entered_value(linestring_layer, field_name=field_name)

        make_field_unique(linestring_layer, field_name="admin_id")

        if dropdown_widget:
            set_field_widget(
                linestring_layer, route_element_type_column, dropdown_widget
            )

        added_layers.append(linestring_layer)

    return added_layers
