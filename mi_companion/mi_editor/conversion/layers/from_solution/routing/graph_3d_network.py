import logging
from typing import Iterable

import shapely

from jord.qgis_utilities.fields import (
    make_field_not_null,
    make_field_reuse_last_entered_value,
)
from jord.qgis_utilities.styling import set_3d_view_settings
from jord.qlive_utilities import add_wkb_layer
from mi_companion import (
    FLOOR_HEIGHT,
    GRAPH_EDGE_COLOR,
    GRAPH_EDGE_WIDTH,
    HALF_SIZE,
)
from mi_companion.layer_descriptors import GRAPH_LINES_DESCRIPTOR
from mi_companion.mi_editor.conversion.layers.from_solution.routing.styling.graduated import (
    set_m_based_graduated_styling,
)
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_qgis,
    solve_target_crs_authid,
)

logger = logging.getLogger(__name__)

__all__ = ["add_graph_3d_network_layers"]

EDGE_BASED_LEVELS = False  # OSM EXPORTER FROM MI SUCKS


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
) -> None:
    """

    :param edge_context_type_dropdown_widget:
    :param graph_group:
    :param highway_type_dropdown_widget:
    :param lines:
    :param lines_meta_data:
    :param points:
    :param points_meta_data:
    :param qgis_instance_handle:
    :return:
    """
    lines = [prepare_geom_for_qgis(l, clean=False) for l in lines]

    logger.info(f"{len(lines)=} loaded!")

    z_augment_lines = []
    geom_measurements = []
    for ith, (line, meta_data) in enumerate(zip(lines, lines_meta_data)):
        edge_levels = meta_data.pop("level").split(";")

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
        measurements = []
        for ith_c, c in enumerate(coords):
            if False:
                if EDGE_BASED_LEVELS:  #
                    if ith_c >= num_coords - 1:
                        level = edge_levels[-1]
                    else:
                        level = edge_levels[ith_c]
                else:
                    level = c[
                        2
                    ]  # * FLOOR_HEIGHT # TODO: FIGURE OUT HOW TO MATCH FLOOR LEVEL

                z_augmented_line_points.append((c[0], c[1], level))
            else:
                level = c[2]

                if False:
                    z_augmented_line_points.append((c[0], c[1], level))

                    measurements.append(
                        FLOOR_HEIGHT / 2.0
                        + level * FLOOR_HEIGHT
                        # Z coordinate is purely for visualisation, measurement is the actual level.
                    )
                else:
                    z_augmented_line_points.append(  # WHEN SHAPELY SUPPORT LINESTRING ZM use the functionality
                        (c[0], c[1], FLOOR_HEIGHT / 2.0 + level * FLOOR_HEIGHT, level)
                    )

        if False:
            geom_measurements.append(measurements)

            z_augment_lines.append(shapely.geometry.LineString(z_augmented_line_points))

        else:
            from osgeo import ogr

            ogr_linestring = ogr.Geometry(ogr.wkbLineString)
            for c in z_augmented_line_points:
                ogr_linestring.AddPointZM(*c)
            z_augment_lines.append(ogr_linestring.ExportToWkb())

    graph_lines_layer = add_wkb_layer(
        qgis_instance_handle=qgis_instance_handle,
        wkbs=z_augment_lines,
        name=GRAPH_LINES_DESCRIPTOR,
        group=graph_group,
        columns=lines_meta_data,
        measurements=measurements,
        categorise_by_attribute="highway",
        visible=True,
        crs=solve_target_crs_authid(),
    )
    if True:
        set_3d_view_settings(  # MAKE offset CONDITIONAL ON FLOOR_INDEX column
            graph_lines_layer,
            offset=FLOOR_HEIGHT * HALF_SIZE,
            edge_width=GRAPH_EDGE_WIDTH,
            color=GRAPH_EDGE_COLOR,
            extrusion=GRAPH_EDGE_WIDTH,
        )

        set_m_based_graduated_styling(
            layers=graph_lines_layer,
        )

        # set_geometry_constraints(graph_lines_layer)

    for a in (graph_lines_layer,):
        if a is not None:
            for field_name in ("abutters", "highway"):
                make_field_not_null(a, field_name=field_name)
                make_field_reuse_last_entered_value(
                    layers=graph_lines_layer, field_name=field_name
                )

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
