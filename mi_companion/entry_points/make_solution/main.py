#!/usr/bin/python
import logging
import uuid
from typing import Optional

SOME_COMMENT_IGNORE_THIS = """
    decimal                            Distinguisable                          N/S or E/W  | E/W     E/W      E/W
places  degrees     DMS                at this scale                           at equator  | 23N/S   45N/S    67N/S
________________________________________________________________________________________________________________________
0       1.0         1° 00′ 0″           country or large region                 111 km      | 102 km  78.7 km  43.5 km
1       0.1         0° 06′ 0″           large city or district                  11.1 km     | 10.2 km 7.87 km  4.35 km
2       0.01        0° 00′ 36″          town or village                         1.11 km     | 1.02 km 0.787 km 0.435 km
3       0.001       0° 00′ 3.6″         neighborhood, street                    111 m       | 102 m   78.7 m   43.5 m
4       0.0001      0° 00′ 0.36″        individual street, large buildings      11.1 m      | 10.2 m  7.87 m   4.35 m
5       0.00001     0° 00′ 0.036″       individual trees, houses                1.11 m      | 1.02 m  0.787 m  0.435 m
6       0.000001    0° 00′ 0.0036″      individual humans                       111 mm      | 102 mm  78.7 mm  43.5 mm
7       0.0000001   0° 00′ 0.00036″     practical limit of commercial surveying 11.1 mm     | 10.2 mm 7.87 mm  4.35 mm
8       0.00000001  0° 00′ 0.000036″    specialized surveying                   1.11 mm     | 1.02 mm 0.787 mm 0.435 mm
________________________________________________________________________________________________________________________
https://en.wikipedia.org/wiki/Decimal_degrees#:~:text=Decimal%20degrees%20(DD)%20is%20a,as%20OpenStreetMap%2C%20and%20GPS%20devices
"""

logger = logging.getLogger(__name__)


def run(
    *,
    name: str = "New Solution",
    customer_id: str = "4ba27f32c1034ca880431259",
    wgs84_degree_lat: Optional[float] = None,
    wgs84_degree_long: Optional[float] = None,
    wgs84_degree_venue_size_sq: float = 1e-4,
) -> None:
    import shapely
    from jord.shapely_utilities import dilate
    from mi_companion.mi_editor.conversion.layers.from_solution.solution import (
        add_solution_layers,
    )

    if wgs84_degree_lat is None:
        wgs84_degree_lat = 0

    if wgs84_degree_long is None:
        wgs84_degree_long = 0

    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    # noinspection PyUnresolvedReferences
    # from qgis.utils import iface

    from integration_system.model import Solution

    s = Solution(uuid.uuid4().hex, name, customer_id=customer_id)
    venue_name = "Empty Venue"
    venue_polygon = dilate(
        shapely.Point(wgs84_degree_lat, wgs84_degree_long),
        distance=wgs84_degree_venue_size_sq,
        cap_style=shapely.BufferCapStyle.square,
    )
    venue_key = s.add_venue(venue_name, venue_name, polygon=venue_polygon)
    building_key = s.add_building(
        venue_name, venue_name, polygon=venue_polygon, venue_key=venue_key
    )
    floor_key = s.add_floor(
        floor_index=0, building_key=building_key, name=venue_name, polygon=venue_polygon
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
