import logging
from typing import Iterable
from xml.etree.ElementTree import ParseError

from jord.qlive_utilities import add_shapely_layer

from mi_companion.configuration.constants import (
    VENUE_DESCRIPTOR,
    ALLOW_DUPLICATE_VENUES_IN_PROJECT,
    ADD_GRAPH,
    GRAPH_DESCRIPTOR,
    SHOW_GRAPH_ON_LOAD,
    NAVIGATION_LINES_DESCRIPTOR,
    NAVIGATION_POINT_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
)
from .building import add_building_layers
from mi_companion.mi_editor.conversion.graph.to_lines import osm_xml_to_lines


logger = logging.getLogger(__name__)

__all__ = ["add_venue_layer"]


def add_venue_layer(
    available_location_type_dropdown_widget,
    door_type_dropdown_widget,
    highway_type_dropdown_widget,
    progress_bar,
    qgis_instance_handle,
    solution,
    solution_group,
):
    for venue in solution.venues:
        if venue is None:
            logger.warning("Venue was None!")
            continue

        venue_name = f"{venue.name} {VENUE_DESCRIPTOR}"

        venue_group = solution_group.findGroup(venue_name)
        if (
            not ALLOW_DUPLICATE_VENUES_IN_PROJECT
        ):  # TODO: base this in external ids instead
            if venue_group:
                logger.error("Venue already loaded!")
                continue

        venue_group = solution_group.insertGroup(0, venue_name)
        venue_group.setExpanded(True)
        venue_group.setExpanded(False)

        if ADD_GRAPH:  # add graph
            try:
                if venue.graph and venue.graph.osm_xml:
                    (lines, lines_meta_data), (
                        points,
                        points_meta_data,
                    ) = osm_xml_to_lines(venue.graph.osm_xml)

                    logger.info(f"{len(lines)=} loaded!")

                    graph_name = f"{venue.graph.graph_id} {GRAPH_DESCRIPTOR}"

                    graph_group = venue_group.insertGroup(0, graph_name)
                    if not SHOW_GRAPH_ON_LOAD:
                        graph_group.setExpanded(True)
                        graph_group.setExpanded(False)
                        graph_group.setItemVisibilityChecked(False)

                    graph_lines_layer = add_shapely_layer(
                        qgis_instance_handle=qgis_instance_handle,
                        geoms=lines,
                        name=NAVIGATION_LINES_DESCRIPTOR,
                        group=graph_group,
                        columns=lines_meta_data,
                        categorise_by_attribute="highway",
                        visible=True,
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
                            visible=SHOW_GRAPH_ON_LOAD,
                        )
                else:
                    logger.warning(f"Venue does not have a valid graph {venue.graph}")

            except ParseError as e:
                logger.error(e)

        add_shapely_layer(
            qgis_instance_handle=qgis_instance_handle,
            geoms=[venue.polygon],
            name=VENUE_POLYGON_DESCRIPTOR,
            columns=[
                {
                    "external_id": venue.external_id,
                    "name": venue.name,
                    "last_verified": venue.last_verified,
                    **(
                        {
                            f"custom_properties.{lang}.{prop}": str(v)
                            for lang, props_map in venue.custom_properties.items()
                            for prop, v in props_map.items()
                        }
                        if venue.custom_properties
                        else {}
                    ),
                }
            ],
            group=venue_group,
            visible=False,
        )

        if progress_bar:
            progress_bar.setValue(20)

        add_building_layers(
            solution=solution,
            progress_bar=progress_bar,
            venue=venue,
            venue_group=venue_group,
            qgis_instance_handle=qgis_instance_handle,
            available_location_type_map_widget=available_location_type_dropdown_widget,
            door_type_dropdown_widget=door_type_dropdown_widget,
        )
