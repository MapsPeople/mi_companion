import logging
import shapely
from typing import Iterable, Mapping

from jord.qgis_utilities import make_field_not_null, set_3d_view_settings
from jord.qlive_utilities import add_shapely_layer
from mi_companion import (
    FLOOR_HEIGHT,
    GRAPH_EDGE_COLOR,
    GRAPH_EDGE_WIDTH,
    HALF_SIZE,
)
from mi_companion.configuration import read_bool_setting
from mi_companion.layer_descriptors import (
    NAVIGATION_HORIZONTAL_LINES_DESCRIPTOR,
    NAVIGATION_POINT_DESCRIPTOR,
    NAVIGATION_VERTICAL_LINES_DESCRIPTOR,
)
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_editing_qgis,
    solve_target_crs_authid,
)

logger = logging.getLogger(__name__)

__all__ = ["add_graph_network_layers", "is_vertical_edge"]


def add_graph_network_layers(
    *,
    edge_context_type_dropdown_widget,
    graph_group,
    highway_type_dropdown_widget,
    lines,
    lines_meta_data,
    points,
    points_meta_data,
    qgis_instance_handle,
):
    if True:
        lines = [prepare_geom_for_editing_qgis(l, clean=False) for l in lines]

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
            if False:
                set_3d_view_settings(  # MAKE offset CONDITIONAL ON FLOOR_INDEX column
                    graph_lines_layer_horizontal,
                    offset=FLOOR_HEIGHT * HALF_SIZE,
                    edge_width=GRAPH_EDGE_WIDTH,
                    color=GRAPH_EDGE_COLOR,
                    extrusion=GRAPH_EDGE_WIDTH,
                )

        graph_lines_layer_vertical = None
        if False:
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
                if False:
                    set_3d_view_settings(graph_lines_layer_vertical)

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
        if a is not None:
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
                                        layer.fields().indexFromName("abutters"),
                                        edge_context_type_dropdown_widget,
                                    )
                        else:
                            layers_inner.setEditorWidgetSetup(
                                layers_inner.fields().indexFromName("abutters"),
                                edge_context_type_dropdown_widget,
                            )
    if False:
        points = [prepare_geom_for_editing_qgis(p, clean=False) for p in points]
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
        points = [prepare_geom_for_editing_qgis(p, clean=False) for p in points]
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


def is_vertical_edge(meta: Mapping[str, str]) -> bool:
    if meta["highway"] == "footway":
        return False
    elif meta["highway"] == "residential":
        return False

    return True
