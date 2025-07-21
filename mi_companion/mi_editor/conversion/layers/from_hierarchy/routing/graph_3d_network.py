import logging

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsGeometry,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsPoint,
    QgsProject,
    QgsWkbTypes,
)
from typing import Any, List, Optional

from integration_system.model import FALLBACK_OSM_GRAPH, Solution
from integration_system.tools.graph_utilities import lines_3d_to_osm_xml
from jord.qgis_utilities import feature_to_shapely, parse_q_value
from mi_companion.configuration import read_bool_setting
from mi_companion.layer_descriptors import GRAPH_LINES_DESCRIPTOR
from mi_companion.mi_editor.conversion.layers.from_hierarchy.constants import (
    DISABLE_GRAPH_EDIT,
)
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis

logger = logging.getLogger(__name__)

__all__ = ["add_3d_graph_edges"]


def set_z_from_m(layer_feature: Any) -> Any:
    """
    Sets z coordinates from m values for the feature geometry

    :param layer_feature:
    :return:
    """

    if not layer_feature:
        logger.error("Feature was None")
        return

    geom = layer_feature.geometry()
    if not geom:
        logger.error("No geometry found")
        return layer_feature

    # Validate M dimension
    if not QgsWkbTypes.hasM(geom.wkbType()):
        logger.error("Geometry does not have M values")
        return layer_feature

    # Extract vertices with M values
    vertices = geom.vertices()
    new_vertices = []

    while vertices.hasNext():
        vertex = vertices.next()
        assert vertex.m() is not None, f"M value missing for vertex {vertex}"
        new_vertices.append(QgsPoint(vertex.x(), vertex.y(), vertex.m()))

    # Create new geometry
    geom_type = QgsWkbTypes.geometryType(geom.wkbType())
    if geom_type == QgsWkbTypes.PointGeometry:
        assert len(new_vertices) == 1, "Point geometry must have exactly one vertex"
        new_geom = QgsGeometry.fromPointXYZ(
            new_vertices[0].x(), new_vertices[0].y(), new_vertices[0].z()
        )

    elif geom_type == QgsWkbTypes.LineGeometry:
        assert len(new_vertices) >= 2, "Line geometry must have at least two vertices"
        new_geom = QgsGeometry.fromPolyline(new_vertices)

    elif geom_type == QgsWkbTypes.PolygonGeometry:
        rings = geom.asPolygon()
        assert rings, "Invalid polygon geometry"
        new_rings = []
        vertex_index = 0
        for ring in rings:
            assert len(ring) >= 4, "Polygon ring must have at least 4 vertices"
            ring_vertices = []
            for _ in ring:
                if vertex_index < len(new_vertices):
                    ring_vertices.append(new_vertices[vertex_index])
                    vertex_index += 1
            new_rings.append(ring_vertices)
        new_geom = QgsGeometry.fromPolygonXYZ(new_rings)

    else:
        logger.error(f"Unsupported geometry type: {geom_type}")
        return layer_feature

    layer_feature.setGeometry(new_geom)
    return layer_feature


def add_3d_graph_edges(
    *,
    graph_key: str,
    graph_group: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param graph_key:
    :param graph_group:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    if not read_bool_setting("UPLOAD_OSM_GRAPH") or DISABLE_GRAPH_EDIT:
        logger.warning("OSM graph upload is disabled")
        return

    lines = []

    for location_group_item in graph_group.children():
        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and GRAPH_LINES_DESCRIPTOR in location_group_item.name()
        ):
            layer = location_group_item.layer()

            if layer:
                for ith, layer_feature in enumerate(layer.getFeatures()):
                    feature_attributes = {
                        k.name(): parse_q_value(v)
                        for k, v in zip(
                            layer_feature.fields(),
                            layer_feature.attributes(),
                        )
                    }

                    feature_attributes["osmid"] = str(-ith)

                    layer_feature = set_z_from_m(layer_feature)

                    graph_line = prepare_geom_for_mi_db_qgis(
                        feature_to_shapely(layer_feature, validate=False), clean=False
                    )

                    lines.append((graph_line, feature_attributes))

    try:
        osm_xml = lines_3d_to_osm_xml(lines).decode(
            "utf-8"
        )  # OSMNX HAS SOME WEIRD BUGS!
    except Exception as e:
        logger.error(e)
        osm_xml = FALLBACK_OSM_GRAPH
        if True:
            raise e

    try:
        solution.update_graph(graph_key, osm_xml=osm_xml)
    except Exception as e:
        _invalid = f"Invalid graph: {e}"
        logger.error(_invalid)
        if collect_invalid:
            issues.append(_invalid)
        else:
            raise e
