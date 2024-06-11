import logging
from typing import Any, Callable, Iterable, Optional
from xml.etree.ElementTree import ParseError

from integration_system.model import Solution
from jord.qlive_utilities import add_shapely_layer

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

from mi_companion.configuration.constants import (
    ALLOW_DUPLICATE_VENUES_IN_PROJECT,
    GRAPH_DESCRIPTOR,
    NAVIGATION_LINES_DESCRIPTOR,
    NAVIGATION_POINT_DESCRIPTOR,
    VENUE_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.graph.to_lines import osm_xml_to_lines
from .building import add_building_layers
from .fields import make_field_unique
from ...projection import (
    GDS_EPSG_NUMBER,
    INSERT_INDEX,
    MI_EPSG_NUMBER,
    prepare_geom_for_qgis,
    should_reproject,
)

logger = logging.getLogger(__name__)

__all__ = ["add_venue_layer"]


def add_venue_layer(
    *,
    available_location_type_dropdown_widget: Any,
    door_type_dropdown_widget: Any,
    highway_type_dropdown_widget: Any,
    venue_type_dropdown_widget: Any,
    progress_bar: Optional[Any],
    qgis_instance_handle: Any,
    solution: Solution,
    solution_group: Any,
) -> None:
    for venue in solution.venues:
        if venue is None:
            logger.warning("Venue was None!")
            continue

        venue_name = f"{venue.name} {VENUE_DESCRIPTOR}"

        venue_group = solution_group.findGroup(venue_name)
        if (
            not ALLOW_DUPLICATE_VENUES_IN_PROJECT
        ):  # TODO: base this in external ids rather than group name
            if venue_group:
                logger.error(f"Venue {venue.name} already loaded!")
                reply = QtWidgets.QMessageBox.question(
                    None,
                    f'f"Venue {venue.name} already loaded!"',
                    f"Would you like to reload the {venue.name} venue from the MI Database?",
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    solution_group.removeChildNode(venue_group)
                else:
                    continue

        venue_group = solution_group.insertGroup(
            INSERT_INDEX, venue_name
        )  # Skip solution data
        venue_group.setExpanded(True)
        venue_group.setExpanded(False)

        venue_layer = add_shapely_layer(
            qgis_instance_handle=qgis_instance_handle,
            geoms=[prepare_geom_for_qgis(venue.polygon)],
            name=VENUE_POLYGON_DESCRIPTOR,
            columns=[
                {
                    "external_id": venue.external_id,
                    "name": venue.name,
                    "last_verified": venue.last_verified,
                    "venue_type": venue.venue_type.name,
                    f"address.city": venue.address.city,
                    f"address.region": venue.address.region,
                    f"address.country": venue.address.country,
                    f"address.street1": venue.address.street1,
                    f"address.postal_code": venue.address.postal_code,
                    f"address.street2": venue.address.street2,
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
            crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
        )

        if venue_type_dropdown_widget:
            for layers_inner in venue_layer:
                if layers_inner:
                    if isinstance(layers_inner, Iterable):
                        for layer in layers_inner:
                            if layer:
                                layer.setEditorWidgetSetup(
                                    layer.fields().indexFromName("venue_type"),
                                    venue_type_dropdown_widget,
                                )
                    else:
                        layers_inner.setEditorWidgetSetup(
                            layers_inner.fields().indexFromName("venue_type"),
                            venue_type_dropdown_widget,
                        )

        make_field_unique(venue_layer)

        if read_bool_setting("ADD_GRAPH"):  # add graph
            try:
                if venue.graph and venue.graph.osm_xml:
                    (lines, lines_meta_data), (
                        points,
                        points_meta_data,
                    ) = osm_xml_to_lines(venue.graph.osm_xml)

                    lines = [prepare_geom_for_qgis(l) for l in lines]
                    points = [prepare_geom_for_qgis(l) for l in points]

                    logger.info(f"{len(lines)=} loaded!")

                    graph_name = f"{venue.graph.graph_id} {GRAPH_DESCRIPTOR}"

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
                        categorise_by_attribute="highway",
                        visible=True,
                        crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
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
                            crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
                        )
                else:
                    logger.warning(f"Venue does not have a valid graph {venue.graph}")

            except ParseError as e:
                logger.error(e)

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
