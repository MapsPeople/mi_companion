import logging
from typing import Iterable
from xml.etree.ElementTree import ParseError

from jord.qlive_utilities import add_shapely_layer

from mi_companion.configuration.constants import (
    GRAPH_DESCRIPTOR,
    NAVIGATION_LINES_DESCRIPTOR,
    NAVIGATION_POINT_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.graph.to_lines import osm_xml_to_lines
from mi_companion.mi_editor.conversion.layers.from_solution.doors import (
    add_route_element_layers,
)
from mi_companion.mi_editor.conversion.projection import (
    GDS_EPSG_NUMBER,
    INSERT_INDEX,
    MI_EPSG_NUMBER,
    prepare_geom_for_qgis,
    should_reproject,
)

logger = logging.getLogger(__name__)


def add_graph_layers(
    *,
    graph,
    venue_group,
    qgis_instance_handle,
    highway_type_dropdown_widget,
    door_type_dropdown_widget,
    solution,
):
    try:
        if graph.osm_xml:
            (lines, lines_meta_data), (
                points,
                points_meta_data,
            ) = osm_xml_to_lines(graph.osm_xml)

            lines = [prepare_geom_for_qgis(l) for l in lines]
            points = [prepare_geom_for_qgis(p) for p in points]

            logger.info(f"{len(lines)=} loaded!")

            graph_name = f"{graph.graph_id} {GRAPH_DESCRIPTOR}"

            graph_group = venue_group.insertGroup(INSERT_INDEX, graph_name)
            if not read_bool_setting("SHOW_GRAPH_ON_LOAD"):
                graph_group.setExpanded(True)
                graph_group.setExpanded(False)
                graph_group.setItemVisibilityChecked(False)

            graph_lines_layer = add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=lines,
                name=NAVIGATION_LINES_DESCRIPTOR,
                group=graph_group,
                columns=lines_meta_data,
                categorise_by_attribute="level",
                visible=True,
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

            if read_bool_setting("ADD_DOORS"):
                add_route_element_layers(
                    graph=graph,
                    qgis_instance_handle=qgis_instance_handle,
                    graph_group=graph_group,
                    dropdown_widget=door_type_dropdown_widget,
                    solution=solution,
                )
        else:
            logger.warning(f"Venue does not have a valid graph {graph}")

    except ParseError as e:
        logger.error(e)
