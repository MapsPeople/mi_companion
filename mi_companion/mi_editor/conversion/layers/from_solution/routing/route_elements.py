import logging
from collections import defaultdict
from typing import Any, Optional

from jord.qgis_utilities.fields import (
    add_dropdown_widget,
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
)
from jord.qgis_utilities.styling import set_3d_view_settings
from jord.qlive_utilities import add_dataframe_layer

from integration_system.model import (
    Avoid,
    Barrier,
    Connection,
    Door,
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
    DOOR_HEIGHT_FACTOR,
    DOOR_LINE_COLOR,
    DOOR_LINE_WIDTH,
    ENTRY_POINTS_DESCRIPTOR,
    FLOOR_HEIGHT,
    FLOOR_VERTICAL_SPACING,
    OBSTACLES_DESCRIPTOR,
    PREFERS_DESCRIPTOR,
    SPLIT_LEVELS_INTO_INDIVIDUAL_GROUPS,
)
from .connections import add_connection_layers
from .linestring_route_elements import add_linestring_route_element_layers
from .point_route_elements import add_point_route_element_layers
from .polygon_route_elements import add_polygon_route_element_layers

logger = logging.getLogger(__name__)

__all__ = ["add_route_element_layers"]


def add_route_element_layers(
    *,
    qgis_instance_handle: Any,
    graph_group: Any,
    graph: Graph,
    solution: Solution,
    door_type_dropdown_widget: Optional[Any] = None,
    connection_type_dropdown_widget: Optional[Any] = None,
    entry_point_type_dropdown_widget: Optional[Any] = None,
) -> None:
    """

    :param qgis_instance_handle:
    :param graph_group:
    :param graph:
    :param solution:
    :param door_type_dropdown_widget:
    :param connection_type_dropdown_widget:
    :param entry_point_type_dropdown_widget:
    :return:
    """

    if SPLIT_LEVELS_INTO_INDIVIDUAL_GROUPS:
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

        if False:  # TODO: IMPLEMENT, DIFFERENT DISPLAY MODE
            unique_levels = sorted(list(unique_levels))
            for level in unique_levels:
                ...  # TODO: NOT IMPLEMENTED YET

    else:
        door_layers = add_linestring_route_element_layers(
            dropdown_widget=door_type_dropdown_widget,
            graph=graph,
            graph_group=graph_group,
            qgis_instance_handle=qgis_instance_handle,
            doors=solution.doors,
        )

        for field_name in ("door_type",):
            make_field_reuse_last_entered_value(door_layers, field_name=field_name)

        if False:
            set_3d_view_settings(  # MAKE offset CONDITIONAL ON FLOOR_INDEX column
                door_layers,
                offset=FLOOR_VERTICAL_SPACING,
                edge_width=DOOR_LINE_WIDTH,
                color=DOOR_LINE_COLOR,
                extrusion=FLOOR_HEIGHT * DOOR_HEIGHT_FACTOR,
            )

        for desc, col in {
            AVOIDS_DESCRIPTOR: solution.avoids,
            PREFERS_DESCRIPTOR: solution.prefers,
            BARRIERS_DESCRIPTOR: solution.barriers,
            ENTRY_POINTS_DESCRIPTOR: solution.entry_points,
        }.items():
            dropdown_widget = None
            route_element_type_column = None

            if desc == ENTRY_POINTS_DESCRIPTOR:
                dropdown_widget = entry_point_type_dropdown_widget
                route_element_type_column = "entry_point_type"

            added_point_layers = add_point_route_element_layers(
                graph=graph,
                graph_group=graph_group,
                qgis_instance_handle=qgis_instance_handle,
                route_element_collection=col,
                layer_descriptor=desc,
                dropdown_widget=dropdown_widget,
                route_element_type_column=route_element_type_column,
            )

            if desc == ENTRY_POINTS_DESCRIPTOR:
                for field_name in ("entry_point_type",):
                    make_field_reuse_last_entered_value(
                        added_point_layers, field_name=field_name
                    )

        add_polygon_route_element_layers(
            graph=graph,
            graph_group=graph_group,
            qgis_instance_handle=qgis_instance_handle,
            route_element_collection=solution.obstacles,
            layer_name=OBSTACLES_DESCRIPTOR,
        )

        add_connection_layers(
            dropdown_widget=connection_type_dropdown_widget,
            graph_group=graph_group,
            qgis_instance_handle=qgis_instance_handle,
            connections=solution.connections,
            graph=graph,
        )
