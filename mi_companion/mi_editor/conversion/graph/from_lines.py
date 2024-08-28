from typing import Optional

import shapely
from networkx import MultiDiGraph
from warg import ensure_existence

from mi_companion.constants import PROJECT_APP_PATH

__all__ = ["lines_to_osm_lines"]


def network_to_osm_xml(osm_xml: MultiDiGraph) -> bytes:
    import osmnx

    osm_cache_path = ensure_existence(PROJECT_APP_PATH.site_cache) / "to_upload.xml"
    osmnx.save_graph_xml(osm_xml, osm_cache_path)
    with open(osm_cache_path, "rb") as f:
        return f.read()


def lines_to_network(
    edges: shapely.MultiLineString, vertices: Optional[shapely.MultiPoint] = None
) -> MultiDiGraph:
    """
        This function is the inverse of graph_to_gdfs and is designed to work in conjunction with it.
    However, you can convert arbitrary node and edge GeoDataFrames as long as 1) gdf_nodes is uniquely indexed
    by osmid, 2) gdf_nodes contains x and y coordinate columns representing node geometries, 3) gdf_edges is
    uniquely multi-indexed by u, v, key (following normal MultiDiGraph structure). This allows you to load any
    node/edge shapefiles or GeoPackage layers as GeoDataFrames then convert them to a MultiDiGraph for graph
    analysis. Note that any geometry attribute on gdf_nodes is discarded since x and y provide the necessary
    node geometry information instead

        :param edges:
        :param vertices:
        :return:
    """

    import osmnx

    g = MultiDiGraph()
    if vertices is not None:
        for ith_node, node in enumerate(vertices.geoms):
            node: shapely.Point
            g.add_node(ith_node, x=node.x, y=node.y)

    for edge in edges.geoms:
        g.add_edge(edge)
        osmnx.nearest_edges()

    osmnx.graph_from_gdfs()

    # osmnx.load_graphml()
    # osmnx.save_graphml()

    return g


def lines_to_osm_lines(lines: shapely.MultiLineString) -> bytes:
    network = lines_to_network(lines)
    return network_to_osm_xml(network)
