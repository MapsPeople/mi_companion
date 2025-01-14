import logging
from typing import Any, Iterable, Mapping, Optional
from xml.etree.ElementTree import ParseError

import shapely
from jord.qgis_utilities.fields import make_field_not_null
from jord.qlive_utilities import add_shapely_layer

from integration_system.graph_utilities import osm_xml_to_lines
from integration_system.model import Graph, Solution, Venue
from mi_companion import (
    DESCRIPTOR_BEFORE,
    GRAPH_DATA_DESCRIPTOR,
    GRAPH_DESCRIPTOR,
    NAVIGATION_HORIZONTAL_LINES_DESCRIPTOR,
    NAVIGATION_POINT_DESCRIPTOR,
    NAVIGATION_VERTICAL_LINES_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_solution.route_elements import (
    add_route_element_layers,
)
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_qgis,
    solve_target_crs_authid,
)

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
                crs=solve_target_crs_authid(),
            )

            if True:
                lines = [prepare_geom_for_qgis(l, clean=False) for l in lines]

                horizontals = list(
                    zip(
                        *[
                            (l, meta)
                            for l, meta in zip(lines, lines_meta_data, strict=True)
                            if not is_vertical_edge(meta)
                        ],
                        strict=True,
                    )
                )
                verticals = list(
                    zip(
                        *[
                            (l, meta)
                            for l, meta in zip(lines, lines_meta_data, strict=True)
                            if is_vertical_edge(meta)
                        ],
                        strict=True,
                    )
                )

                logger.info(f"{len(lines)=} loaded!")
                graph_lines_layer_horizontal = None
                if horizontals:
                    horizontal_lines, horizontal_lines_meta_data = horizontals
                    graph_lines_layer_horizontal = add_shapely_layer(
                        qgis_instance_handle=qgis_instance_handle,
                        geoms=horizontal_lines,
                        name=NAVIGATION_HORIZONTAL_LINES_DESCRIPTOR,
                        group=graph_group,
                        columns=horizontal_lines_meta_data,
                        categorise_by_attribute="level",
                        visible=read_bool_setting(
                            "SHOW_GRAPH_ON_LOAD",
                        ),
                        crs=solve_target_crs_authid(),
                    )

                graph_lines_layer_vertical = None
                if verticals:
                    vertical_lines, vertical_lines_meta_data = verticals

                    vertical_points = []
                    vertical_points_meta_data = []

                    for ith, (line, meta_data) in enumerate(
                        zip(vertical_lines, vertical_lines_meta_data)
                    ):
                        meta_data["vertical_id"] = meta_data["osmid"]
                        if False:
                            levels = meta_data["level"].split(";")

                            coords = line.coords
                            num_coords = len(coords)

                            for ith_c, c in enumerate(coords):
                                meta_data_copy = meta_data.copy()
                                vertical_points.append(shapely.geometry.Point(c))
                                if ith_c >= num_coords - 1:
                                    meta_data_copy["level"] = levels[-1]
                                else:
                                    meta_data_copy["level"] = levels[ith_c]
                                vertical_points_meta_data.append(meta_data_copy)
                        else:
                            ...

                    graph_lines_layer_vertical = add_shapely_layer(
                        qgis_instance_handle=qgis_instance_handle,
                        geoms=vertical_points,
                        name=NAVIGATION_VERTICAL_LINES_DESCRIPTOR,
                        group=graph_group,
                        columns=vertical_points_meta_data,
                        categorise_by_attribute="vertical_id",
                        visible=read_bool_setting(
                            "SHOW_GRAPH_ON_LOAD",
                        ),
                        crs=solve_target_crs_authid(),
                    )

                    for field_name in ("vertical_id",):
                        make_field_not_null(
                            graph_lines_layer_vertical, field_name=field_name
                        )

            # TODO: ADD graph_bounds to a poly layer
            for a in (
                graph_lines_layer_horizontal,
                graph_lines_layer_vertical,
            ):  # TODO: Vertical level based in node context rather than edge
                # context, because edge context is wrong ATM
                if a:
                    for field_name in ("level", "abutters", "highway"):
                        make_field_not_null(a, field_name=field_name)

                    if highway_type_dropdown_widget:
                        for layers_inner in a:
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

                    if edge_context_type_dropdown_widget:
                        for layers_inner in a:
                            if layers_inner:
                                if isinstance(layers_inner, Iterable):
                                    for layer in layers_inner:
                                        if layer:
                                            layer.setEditorWidgetSetup(
                                                layer.fields().indexFromName(
                                                    "abutters"
                                                ),
                                                edge_context_type_dropdown_widget,
                                            )
                                else:
                                    layers_inner.setEditorWidgetSetup(
                                        layers_inner.fields().indexFromName("abutters"),
                                        edge_context_type_dropdown_widget,
                                    )

            if False:
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
                    crs=solve_target_crs_authid(),
                )

            if False:
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
                    crs=solve_target_crs_authid(),
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

        # TODO: Add graph bounds to a poly layer

    except ParseError as e:
        logger.error(e)


def is_vertical_edge(meta: Mapping[str, str]) -> bool:
    if meta["highway"] == "footway":
        return False
    elif meta["highway"] == "residential":
        return False

    return True
