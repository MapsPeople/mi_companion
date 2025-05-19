import logging
from typing import Any, Optional
from xml.etree.ElementTree import ParseError

from integration_system.tools.graph_utilities import osm_xml_to_lines
from integration_system.model import Graph, Solution, Venue
from jord.qgis_utilities import make_field_not_null, set_geometry_constraints
from jord.qlive_utilities import add_shapely_layer
from mi_companion import (
    DESCRIPTOR_BEFORE,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.layer_descriptors import (
    GRAPH_BOUND_DESCRIPTOR,
    GRAPH_GROUP_DESCRIPTOR,
)
from mi_companion.mi_editor.conversion.layers.from_solution.routing.graph_3d_network import (
    add_graph_3d_network_layers,
)
from mi_companion.mi_editor.conversion.layers.from_solution.routing.route_elements import (
    add_route_element_layers,
)
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_qgis,
    solve_target_crs_authid,
)

logger = logging.getLogger(__name__)

__all__ = ["add_graph_layers"]


def add_graph_layers(
    *,
    graph: Graph,
    venue_group: Any,
    qgis_instance_handle: Any,
    solution: Solution,
    venue: Venue,
    highway_type_dropdown_widget: Optional[Any] = None,
    door_type_dropdown_widget: Optional[Any] = None,
    connection_type_dropdown_widget: Optional[Any] = None,
    entry_point_type_dropdown_widget: Optional[Any] = None,
    edge_context_type_dropdown_widget: Optional[Any] = None,
) -> None:
    """

    :param graph:
    :param venue_group:
    :param qgis_instance_handle:
    :param solution:
    :param venue:
    :param highway_type_dropdown_widget:
    :param door_type_dropdown_widget:
    :param connection_type_dropdown_widget:
    :param entry_point_type_dropdown_widget:
    :param edge_context_type_dropdown_widget:
    :return:
    """
    try:
        if graph.osm_xml:
            (lines, lines_meta_data), (
                points,
                points_meta_data,
            ) = osm_xml_to_lines(graph.osm_xml)

            if DESCRIPTOR_BEFORE:
                graph_name = f"{GRAPH_GROUP_DESCRIPTOR} {graph.graph_id}"
            else:
                graph_name = f"{graph.graph_id} {GRAPH_GROUP_DESCRIPTOR}"

            graph_group = venue_group.insertGroup(0, graph_name)
            if not read_bool_setting("SHOW_GRAPH_ON_LOAD"):
                graph_group.setExpanded(True)
                graph_group.setExpanded(False)
                graph_group.setItemVisibilityChecked(False)

            graph_boundary = venue.graph.boundary
            if graph_boundary is None:
                logger.warning(
                    f"Graph {graph} has no boundary, defaulting to venue boundary"
                )
                graph_boundary = venue.polygon

            graph_boundary = prepare_geom_for_qgis(graph_boundary, clean=False)

            graph_bound_layer = add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[graph_boundary],
                name=GRAPH_BOUND_DESCRIPTOR,
                group=graph_group,
                columns=[{"graph_id": graph.graph_id}],
                visible=False,
                crs=solve_target_crs_authid(),
            )
            set_geometry_constraints(graph_bound_layer)
            make_field_not_null(graph_bound_layer, field_name="graph_id")

            # add_graph_network_layers(
            add_graph_3d_network_layers(
                edge_context_type_dropdown_widget=edge_context_type_dropdown_widget,
                graph_group=graph_group,
                highway_type_dropdown_widget=highway_type_dropdown_widget,
                lines=lines,
                lines_meta_data=lines_meta_data,
                points=points,
                points_meta_data=points_meta_data,
                qgis_instance_handle=qgis_instance_handle,
            )

            if read_bool_setting("ADD_ROUTE_ELEMENTS"):
                add_route_element_layers(
                    graph=graph,
                    qgis_instance_handle=qgis_instance_handle,
                    graph_group=graph_group,
                    solution=solution,
                    door_type_dropdown_widget=door_type_dropdown_widget,
                    connection_type_dropdown_widget=connection_type_dropdown_widget,
                    entry_point_type_dropdown_widget=entry_point_type_dropdown_widget,
                )
        else:
            logger.warning(f"Venue does not have a valid graph {graph}")

    except ParseError as e:
        logger.error(e)
