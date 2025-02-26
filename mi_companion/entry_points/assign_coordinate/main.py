#!/usr/bin/python
import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CoordinateDimension(str, Enum):
    X = "x"
    Y = "y"
    Z = "z"


def set_coordinate(
    feature: Any, value: float, coord_type: CoordinateDimension = CoordinateDimension.Z
) -> Any:
    """Sets the specified coordinate for all vertices in any feature geometry type"""
    from qgis.core import QgsWkbTypes, QgsPoint, QgsGeometry

    if feature is None:
        logger.error("Feature was None")
        return

    geom = feature.geometry()
    if not geom:
        logger.error("No geometry found")
        return feature

    # Get geometry type
    geom_type = QgsWkbTypes.geometryType(geom.wkbType())

    # Extract vertices
    vertices = geom.vertices()
    new_vertices = []
    while vertices.hasNext():
        vertex = vertices.next()
        coords = {
            "x": value if coord_type == CoordinateDimension.X else vertex.x(),
            "y": value if coord_type == CoordinateDimension.Y else vertex.y(),
            "z": value if coord_type == CoordinateDimension.Z else vertex.z(),
        }
        new_vertices.append(QgsPoint(coords["x"], coords["y"], coords["z"]))

    # Create appropriate geometry type
    if geom_type == QgsWkbTypes.PointGeometry:
        if len(new_vertices) == 1:
            new_geom = QgsGeometry.fromPointXYZ(
                new_vertices[0].x(), new_vertices[0].y(), new_vertices[0].z()
            )
        else:
            new_geom = QgsGeometry.fromMultiPointXYZ(new_vertices)
    elif geom_type == QgsWkbTypes.LineGeometry:
        new_geom = QgsGeometry.fromPolyline(new_vertices)
    elif geom_type == QgsWkbTypes.PolygonGeometry:
        rings = geom.asPolygon()
        new_rings = []
        vertex_index = 0
        for ring in rings:
            ring_vertices = []
            for _ in ring:
                if vertex_index < len(new_vertices):
                    ring_vertices.append(new_vertices[vertex_index])
                    vertex_index += 1
            new_rings.append(ring_vertices)
        new_geom = QgsGeometry.fromPolygonXYZ(new_rings)
    else:
        logger.error(f"Unsupported geometry type: {geom_type}")
        return feature

    feature.setGeometry(new_geom)
    return feature


def run(
    *, value: float = 0.0, dimension: str = "z", only_active_layer: bool = True
) -> None:
    """Assigns a coordinate value to all vertices in selected features of any geometry type"""
    from qgis.utils import iface
    from qgis.core import QgsProject

    if not isinstance(dimension, CoordinateDimension):
        dimension = CoordinateDimension(dimension.lower())

    if only_active_layer:
        layers = list(iface.layerTreeView().selectedLayers())
    else:
        layers = list(QgsProject.instance().mapLayers().values())

    if len(layers) == 0:
        logger.error("No layers were given")
        return

    for layer in layers:
        if layer.selectedFeatureCount() > 0:
            selected_features = layer.selectedFeatures()

            if len(selected_features) > 0:
                for feature in selected_features:
                    logger.info(
                        f"Setting {dimension} coordinate for feature {feature.id()}"
                    )
                    feature = set_coordinate(feature, value, dimension)
                    layer.updateFeature(feature)
            else:
                logger.error("Please select features in the layer")
        else:
            logger.error(
                f"Skipping layer {layer.name()} as it had no selected features"
            )
