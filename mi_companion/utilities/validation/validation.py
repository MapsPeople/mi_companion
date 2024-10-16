import logging

import shapely
from geojson import LineString

from integration_system.mi import get_remote_solution
from integration_system.model import Solution
from mi_companion.utilities.graph.to_lines import osm_xml_to_network

logger = logging.getLogger(__name__)


def validate_venue(*args): ...


def validate_graph(
    solution: Solution, valid_number_of_edge_intersections: int = 2
) -> None:
    for g in solution.graphs:
        graph = osm_xml_to_network(g.osm_xml)
        for edge in graph.edges:
            intersecting_rooms = []
            edge_line = LineString(edge)

            for r in solution.rooms:
                if r.polygon.intersects(edge_line):
                    intersecting_rooms.append(
                        (r, shapely.intersection(r.polygon, edge_line))
                    )

            if len(intersecting_rooms) > valid_number_of_edge_intersections:
                logger.error(
                    f"{edge} is intersecting {len(intersecting_rooms)} room polygons"
                )
                logger.error(f"{intersecting_rooms}")

    for node in solution.nodes:
        node


if __name__ == "__main__":
    solution = get_remote_solution("chen-dfw")
    validate_graph(solution)
