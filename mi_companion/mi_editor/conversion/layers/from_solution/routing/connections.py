import logging
from typing import Any, List, Optional

import geopandas
from geopandas import GeoDataFrame
from pandas import json_normalize

from integration_system.model import ConnectionCollection, Graph
from jord.qgis_utilities import (
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
    set_field_widget,
)
from jord.qlive_utilities import add_dataframe_layer
from mi_companion import INSERT_INDEX, MAKE_FLOOR_WISE_LAYERS
from mi_companion.layer_descriptors import CONNECTORS_GROUP_DESCRIPTOR
from mi_companion.mi_editor.conversion.projection import (
    reproject_geometry_df,
    solve_target_crs_authid,
)

logger = logging.getLogger(__name__)

__all__ = ["add_connection_layers"]


def add_connection_layers(
    *,
    graph_group: Any,
    qgis_instance_handle: Any,
    graph: Graph,
    connections: ConnectionCollection,
    dropdown_widget: Optional[Any] = None,
    route_element_type_column: Optional[str] = "connection_type",
) -> List[Any]:
    """

    :param graph_group:
    :param qgis_instance_handle:
    :param graph:
    :param connections:
    :param dropdown_widget:
    :param route_element_type_column:
    :return:
    """
    added_layers = []

    connectors = {}
    for c in connections:
        for connector_key, connector in c.connectors.items():
            a = {}
            if connector.fields is not None:
                a = json_normalize(connector.fields)

            connectors[connector.admin_id] = {
                "floor_index": connector.floor_index,
                "point": connector.point,
                "connection_id": c.connection_id,
                "connection_type": c.connection_type.value,
                "graph.graph_id": c.graph.graph_id,
                **a,
            }

    if len(connectors) == 0:
        return []

    df = (
        GeoDataFrame.from_dict(connectors, orient="index")
        .reset_index(names="admin_id")
        .set_geometry("point")
    )  # Pandas pain....

    df["floor_index"] = df["floor_index"].astype(str)

    if MAKE_FLOOR_WISE_LAYERS:
        doors_group = graph_group.insertGroup(INSERT_INDEX, CONNECTORS_GROUP_DESCRIPTOR)

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

                empty_lines = df[df.is_empty]
                if not empty_lines.empty:
                    logger.warning(f"Dropping {empty_lines}")

                df = df[~df.is_empty]

                reproject_geometry_df(door_df)

                connectors_layer = add_dataframe_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    dataframe=door_df,
                    geometry_column="point",
                    name=f"{floor_index}",
                    categorise_by_attribute="floor_index",
                    group=doors_group,
                    crs=solve_target_crs_authid(),
                )
                added_layers.append(connectors_layer)

                make_field_unique(connectors_layer, field_name="admin_id")

                for field_name in ("floor_index", "connection_id", "connection_type"):
                    make_field_not_null(connectors_layer, field_name=field_name)
                    make_field_reuse_last_entered_value(
                        connectors_layer, field_name=field_name
                    )

                if dropdown_widget:
                    set_field_widget(
                        connectors_layer, route_element_type_column, dropdown_widget
                    )
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
            name=CONNECTORS_GROUP_DESCRIPTOR,
            categorise_by_attribute="floor_index",
            group=graph_group,
            crs=solve_target_crs_authid(),
        )

        added_layers.append(connectors_layer)

        for field_name in ("floor_index", "connection_id", "connection_type"):
            make_field_not_null(connectors_layer, field_name=field_name)
            make_field_reuse_last_entered_value(connectors_layer, field_name=field_name)

        make_field_unique(connectors_layer, field_name="admin_id")

        if dropdown_widget:
            set_field_widget(
                connectors_layer, route_element_type_column, dropdown_widget
            )

    return added_layers
