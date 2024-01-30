import osmnx
import shapely
from networkx import MultiDiGraph
from warg import ensure_existence

from ....constants import PROJECT_APP_PATH

__all__ = []


def network_to_osm_xml(osm_xml: MultiDiGraph) -> bytes:
    osm_cache_path = ensure_existence(PROJECT_APP_PATH.site_cache) / "to_upload.xml"
    osmnx.save_graph_xml(osm_xml, osm_cache_path)
    with open(osm_cache_path, "rb") as f:
        return f.read()


def lines_to_network(graph: shapely.MultiLineString) -> MultiDiGraph:
    # osmnx.graph_from_gdfs()
    osmnx.load_graphml()
    osmnx.save_graphml()
    return MultiDiGraph()


def lines_to_osm_lines(lines: shapely.MultiLineString) -> bytes:
    network = lines_to_network(lines)
    return network_to_osm_xml(network)
