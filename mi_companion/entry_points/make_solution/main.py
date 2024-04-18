#!/usr/bin/python
import uuid
from typing import Optional


def run(
    *,
    name: str = "New Solution",
    customer_id: str = "4ba27f32c1034ca880431259",
    lat: Optional[float] = None,
    long: Optional[float] = None,
    size: float = 10
) -> None:
    import shapely
    from jord.shapely_utilities import dilate
    from mi_companion.mi_editor.conversion.layers.from_solution.solution import (
        add_solution_layers,
    )

    if lat is None:
        lat = 0
    if long is None:
        long = 0

    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    # noinspection PyUnresolvedReferences
    # from qgis.utils import iface

    from integration_system.model import Solution

    s = Solution(uuid.uuid4().hex, name, customer_id=customer_id)
    venue_name = "Empty Venue"
    venue_polygon = dilate(shapely.Point(lat, long), distance=size)
    venue_key = s.add_venue(venue_name, venue_name, polygon=venue_polygon)
    building_key = s.add_building(
        venue_name, venue_name, polygon=venue_polygon, venue_key=venue_key
    )
    floor_key = s.add_floor(
        venue_name, venue_name, 0, venue_polygon, building_key=building_key
    )
    s.add_room(venue_name, venue_name, polygon=venue_polygon, floor_key=floor_key)
    s.add_area(venue_name, venue_name, polygon=venue_polygon, floor_key=floor_key)
    s.add_point_of_interest(
        venue_name,
        venue_name,
        venue_polygon.representative_point(),
        floor_key=floor_key,
    )
    # s.add_graph()
    # s.add_door()
    # s.add_connection()

    root = QgsProject.instance().layerTreeRoot()

    add_solution_layers(
        qgis_instance_handle=None,
        solution=s,
        layer_tree_root=QgsProject.instance().layerTreeRoot(),
    )
