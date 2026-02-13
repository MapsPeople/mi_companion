import logging
from osgeo import ogr
from typing import Any

from jord.qgis_utilities import (
    make_field_not_null,
    make_field_reuse_last_entered_value,
    set_3d_view_settings,
    set_field_widget,
)
from jord.qlive_utilities import add_wkb_layer
from mi_companion import (
    FLOOR_HEIGHT,
    GRAPH_EDGE_COLOR,
    GRAPH_EDGE_WIDTH,
    HALF_SIZE,
)
from mi_companion.layer_descriptors import GRAPH_LINES_DESCRIPTOR
from mi_companion.mi_editor.conversion.layers.from_solution.routing.styling import (
    set_graph_styling,
)
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_editing_qgis,
    solve_target_crs_authid,
)

_logger = logging.getLogger(__name__)

__all__ = ["add_navigation_graph_layers"]

EDGE_BASED_LEVELS = False  # OSM EXPORTER FROM MI SUCKS
EDGE_CLASSIFICATION_ATTRIBUTE = "highway"
PERSISTED_EDGE_ATTRIBUTES = (EDGE_CLASSIFICATION_ATTRIBUTE, "abutters")
DROPPED_EDGE_ATTRIBUTES = (
    "from",
    "to",
    "length",
    "distance",
    "oneway",
    "reversed",
    "osmid",
    "level",
)


def add_navigation_graph_layers(
    *,
    edge_context_type_dropdown_widget: Any,
    graph_group: Any,
    highway_type_dropdown_widget: Any,
    lines: Any,
    lines_meta_data: Any,
    qgis_instance_handle: Any,
) -> None:
    """

    :param edge_context_type_dropdown_widget:
    :param graph_group:
    :param highway_type_dropdown_widget:
    :param lines:
    :param lines_meta_data:
    :param qgis_instance_handle:
    :return:
    """

    z_augment_lines = []
    for ith, (line, meta_data) in enumerate(
        zip(
            [prepare_geom_for_editing_qgis(l, clean=False) for l in lines],
            lines_meta_data,
        )
    ):
        # edge_levels = meta_data.pop("level").split(";")

        for a in DROPPED_EDGE_ATTRIBUTES:
            if a in meta_data:
                _ = meta_data.pop(a)

        z_augmented_line_points = []
        for ith_c, (x, y, z) in enumerate(line.coords):
            z_augmented_line_points.append(  # WHEN SHAPELY SUPPORT LINESTRING ZM use the functionality
                (
                    x,  # X
                    y,  # Y
                    FLOOR_HEIGHT / 2.0
                    + z * FLOOR_HEIGHT,  # Z, used for 3d visualisation
                    z,  # M, logical level
                )
            )

        ogr_linestring = ogr.Geometry(ogr.wkbLineString)
        for xyzm in z_augmented_line_points:
            ogr_linestring.AddPointZM(*xyzm)

        z_augment_lines.append(ogr_linestring.ExportToWkb())

    graph_lines_layer = add_wkb_layer(
        qgis_instance_handle=qgis_instance_handle,
        wkbs=z_augment_lines,
        name=GRAPH_LINES_DESCRIPTOR,
        group=graph_group,
        columns=lines_meta_data,
        categorise_by_attribute=EDGE_CLASSIFICATION_ATTRIBUTE,
        visible=True,
        crs=solve_target_crs_authid(),
    )

    set_3d_view_settings(  # MAKE offset CONDITIONAL ON FLOOR_INDEX column
        graph_lines_layer,
        offset=FLOOR_HEIGHT * HALF_SIZE,
        edge_width=GRAPH_EDGE_WIDTH,
        color=GRAPH_EDGE_COLOR,
        extrusion=GRAPH_EDGE_WIDTH,
    )

    set_graph_styling(
        layers=graph_lines_layer,
    )

    if graph_lines_layer is not None:
        for field_name in PERSISTED_EDGE_ATTRIBUTES:
            make_field_not_null(graph_lines_layer, field_name=field_name)
            make_field_reuse_last_entered_value(
                layers=graph_lines_layer, field_name=field_name
            )

        if highway_type_dropdown_widget:
            set_field_widget(
                layers=graph_lines_layer,
                field_name="highway",
                form_widget=highway_type_dropdown_widget,
            )

        if edge_context_type_dropdown_widget:
            set_field_widget(
                layers=graph_lines_layer,
                field_name="abutters",
                form_widget=edge_context_type_dropdown_widget,
            )
