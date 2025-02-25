import logging
from typing import Iterable

import shapely
from jord.qgis_utilities.fields import (
    add_dropdown_widget,
    make_field_not_null,
    make_field_unique,
)
from jord.qgis_utilities.styling import set3dviewsettings
from jord.qlive_utilities import add_dataframe_layer, add_shapely_layer

from mi_companion import (
    FLOOR_HEIGHT,
    GRAPH_EDGE_COLOR,
    GRAPH_EDGE_WIDTH,
    HALF_SIZE,
    NAVIGATION_GRAPH_LINES_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_qgis,
    solve_target_crs_authid,
)

logger = logging.getLogger(__name__)

__all__ = ["add_graph_3d_network_layers"]


def set_z_based_graduated_styling(layer):
    "z_max( @ geometry)"

    pass


def add_graph_3d_network_layers(
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
    lines = [prepare_geom_for_qgis(l, clean=False) for l in lines]

    logger.info(f"{len(lines)=} loaded!")

    z_augment_lines = []

    for ith, (line, meta_data) in enumerate(zip(lines, lines_meta_data)):
        levels = meta_data.pop("level").split(";")
        _ = meta_data.pop("from")
        _ = meta_data.pop("to")
        _ = meta_data.pop("length")
        _ = meta_data.pop("distance")
        _ = meta_data.pop("oneway")
        _ = meta_data.pop("reversed")
        _ = meta_data.pop("osmid")

        coords = line.coords
        num_coords = len(coords)
        z_augmented_line_points = []
        for ith_c, c in enumerate(coords):
            if ith_c >= num_coords - 1:
                level = levels[-1]
            else:
                level = levels[ith_c]

            z_augmented_line_points.append((c[0], c[1], level))

        z_augment_lines.append(shapely.geometry.LineString(z_augmented_line_points))

    graph_lines_layer = add_shapely_layer(
        qgis_instance_handle=qgis_instance_handle,
        geoms=z_augment_lines,
        name=NAVIGATION_GRAPH_LINES_DESCRIPTOR,
        group=graph_group,
        columns=lines_meta_data,
        categorise_by_attribute="highway",
        visible=read_bool_setting(
            "SHOW_GRAPH_ON_LOAD",
        ),
        crs=solve_target_crs_authid(),
    )
    if True:
        set3dviewsettings(  # MAKE offset CONDITIONAL ON FLOOR_INDEX column
            graph_lines_layer,
            offset=FLOOR_HEIGHT * HALF_SIZE,
            edge_width=GRAPH_EDGE_WIDTH,
            color=GRAPH_EDGE_COLOR,
            extrusion=GRAPH_EDGE_WIDTH,
        )

        set_z_based_graduated_styling(
            layer=graph_lines_layer,
        )

    for a in (graph_lines_layer,):
        if a is not None:
            for field_name in ("abutters", "highway"):
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
