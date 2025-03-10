#!/usr/bin/python
import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

__all__ = []


class ValueDimension(str, Enum):
    X = "x"
    Y = "y"
    Z = "z"
    M = "m"


def set_coordinate(
    feature: Any, value: float, coord_type: ValueDimension = ValueDimension.M
) -> Any:
    """


    Sets the specified coordinate for all vertices in any feature geometry type

    :param feature:
    :param value:
    :param coord_type:
    :return:
    """
    from qgis.core import QgsWkbTypes, QgsPoint, QgsGeometry, QgsMultiPoint

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
    new_points = []
    while vertices.hasNext():
        vertex = vertices.next()

        extra_dimensions = {}

        if vertex.is3D():
            extra_dimensions["z"] = (
                value if coord_type == ValueDimension.Z else vertex.z()
            )

        if vertex.isMeasure():
            extra_dimensions["m"] = (
                value if coord_type == ValueDimension.M else vertex.m()
            )

        coords = {
            "x": value if coord_type == ValueDimension.X else vertex.x(),
            "y": value if coord_type == ValueDimension.Y else vertex.y(),
            **extra_dimensions,
        }
        new_points.append(QgsPoint(*coords.values()))

    # Create appropriate geometry type
    if geom_type == QgsWkbTypes.PointGeometry:
        if len(new_points) > 1:
            new_geom = QgsMultiPoint(new_points)
        else:
            new_geom = new_points[0]

    elif geom_type == QgsWkbTypes.LineGeometry:
        new_geom = QgsGeometry.fromPolyline(new_points)

    elif geom_type == QgsWkbTypes.PolygonGeometry:
        rings = geom.asPolygon()
        new_rings = []
        vertex_index = 0
        for ring in rings:
            ring_vertices = []
            for _ in ring:
                if vertex_index < len(new_points):
                    ring_vertices.append(new_points[vertex_index])
                    vertex_index += 1
            new_rings.append(ring_vertices)
        new_geom = QgsGeometry.fromPolygonXY(
            new_rings
        )  # TODO: LOOK INTO WHETHER THIS WITH Z AND M COORDINATE..

    else:
        logger.error(f"Unsupported geometry type: {geom_type}")
        return feature

    feature.setGeometry(new_geom)
    return feature


def run(
    *, value: float = 0.0, dimension: str = "m", only_active_layer: bool = True
) -> None:
    """

    Assigns a coordinate value to all vertices in selected features of any geometry type

    :param value: Value to assign
    :param dimension: Which dimension to assign the value to
    :param only_active_layer: Only apply to active layer
    :return:
    """
    from qgis.utils import iface
    from qgis.core import QgsProject

    if not isinstance(dimension, ValueDimension):
        dimension = ValueDimension(dimension.lower())

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
