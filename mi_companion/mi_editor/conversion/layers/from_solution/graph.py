import logging
from typing import Any, Iterable, Optional
from xml.etree.ElementTree import ParseError

from jord.qlive_utilities import add_shapely_layer

from integration_system.model import Graph, Solution, Venue
from mi_companion import (
    DESCRIPTOR_BEFORE,
    GRAPH_DATA_DESCRIPTOR,
    GRAPH_DESCRIPTOR,
    NAVIGATION_LINES_DESCRIPTOR,
    NAVIGATION_POINT_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_solution.route_elements import (
    add_route_element_layers,
)
from mi_companion.mi_editor.conversion.projection import (
    GDS_EPSG_NUMBER,
    MI_EPSG_NUMBER,
    prepare_geom_for_qgis,
    should_reproject,
)
from mi_companion.utilities.graph import osm_xml_to_lines

logger = logging.getLogger(__name__)


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
) -> None:
    try:
        if graph.osm_xml:
            (lines, lines_meta_data), (
                points,
                points_meta_data,
            ) = osm_xml_to_lines(graph.osm_xml)

            if DESCRIPTOR_BEFORE:
                graph_name = f"{GRAPH_DESCRIPTOR} {graph.graph_id}"
            else:
                graph_name = f"{graph.graph_id} {GRAPH_DESCRIPTOR}"

            graph_group = venue_group.insertGroup(0, graph_name)
            if not read_bool_setting("SHOW_GRAPH_ON_LOAD"):
                graph_group.setExpanded(True)
                graph_group.setExpanded(False)
                graph_group.setItemVisibilityChecked(False)

            graph_meta_point_layer = add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[venue.polygon.representative_point()],
                name=GRAPH_DATA_DESCRIPTOR,
                group=graph_group,
                columns=[{"graph_id": graph.graph_id}],
                visible=False,
                crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
            )

            if True:
                lines = [prepare_geom_for_qgis(l, clean=False) for l in lines]
                logger.info(f"{len(lines)=} loaded!")
                if lines:
                    graph_lines_layer = add_shapely_layer(
                        qgis_instance_handle=qgis_instance_handle,
                        geoms=lines,
                        name=NAVIGATION_LINES_DESCRIPTOR,
                        group=graph_group,
                        columns=lines_meta_data,
                        categorise_by_attribute="level",
                        visible=False,
                        crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
                    )

            if highway_type_dropdown_widget:
                for layers_inner in graph_lines_layer:
                    if layers_inner:
                        if isinstance(layers_inner, Iterable):
                            for layer in layers_inner:
                                if layer:
                                    layer.setEditorWidgetSetup(
                                        layer.fields().indexFromName("highway"),
                                        highway_type_dropdown_widget,
                                    )
                        else:
                            layers_inner.setEditorWidgetSetup(
                                layers_inner.fields().indexFromName("highway"),
                                highway_type_dropdown_widget,
                            )

            if True:  # SHOW POINTs AS WELL
                points = [prepare_geom_for_qgis(p, clean=False) for p in points]
                logger.info(f"{len(points)=} loaded!")
                graph_points_layer = add_shapely_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    geoms=points,
                    name=NAVIGATION_POINT_DESCRIPTOR,
                    group=graph_group,
                    columns=points_meta_data,
                    visible=read_bool_setting(
                        "SHOW_GRAPH_ON_LOAD",
                    ),
                    categorise_by_attribute="level",
                    crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
                )

            if read_bool_setting("ADD_ROUTE_ELEMENTS"):
                add_route_element_layers(
                    graph=graph,
                    qgis_instance_handle=qgis_instance_handle,
                    graph_group=graph_group,
                    solution=solution,
                    door_type_dropdown_widget=door_type_dropdown_widget,
                    connection_type_dropdown_widget=connection_type_dropdown_widget,
                )
        else:
            logger.warning(f"Venue does not have a valid graph {graph}")

    except ParseError as e:
        logger.error(e)
