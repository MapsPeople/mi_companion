from typing import Dict, Tuple, Sized

import geopandas
import osmnx
import shapely
from networkx import MultiDiGraph
from warg import ensure_existence

from mi_companion.constants import PROJECT_APP_PATH

__all__ = ["osm_xml_to_lines"]


def osm_xml_to_network(osm_xml: str) -> MultiDiGraph:
    osm_cache_path = ensure_existence(PROJECT_APP_PATH.site_cache) / "from_mi_rep.xml"
    with open(osm_cache_path, "w") as f:
        f.write(osm_xml)
    return osmnx.graph_from_xml(osm_cache_path)


def network_to_lines(
    graph: MultiDiGraph,
) -> Tuple[Tuple[Sized, Dict], Tuple[Sized, Dict]]:
    if False:
        gpkg_cache_path = (
            ensure_existence(PROJECT_APP_PATH.site_cache) / "to_shape_file.gpkg"
        )
        osmnx.save_graph_geopackage(graph, gpkg_cache_path, directed=True)

        df = geopandas.read_file(str(gpkg_cache_path))
    elif False:
        graphml_cache_path = (
            ensure_existence(PROJECT_APP_PATH.site_cache) / "to_shape_file.xml"
        )
        osmnx.save_graph_graphml(graph, graphml_cache_path, directed=True)
        df = geopandas.read_file(str(graphml_cache_path))
    else:
        line_strings = [
            (
                shapely.LineString(
                    (
                        (graph.nodes[u]["x"], graph.nodes[u]["y"]),
                        (graph.nodes[v]["x"], graph.nodes[v]["y"]),
                    )
                ),
                w,
            )
            for u, v, w in graph.edges(data=True)
        ]
        points = [
            (shapely.Point(w["x"], w["y"]), {"node_id": v, **w})
            for v, w in graph.nodes(data=True)
        ]

    # noinspection PyTypeChecker

    linestring_zips = (*zip(*line_strings),)
    assert len(line_strings) == len(linestring_zips[0])

    point_zips = (*zip(*points),)
    assert len(points) == len(point_zips[0])

    return (linestring_zips, point_zips)


def osm_xml_to_lines(
    osm_xml: str,
) -> tuple[tuple[Sized, dict], tuple[Sized, dict]]:
    (lines, lines_meta_data), (points, points_meta_data) = network_to_lines(
        osm_xml_to_network(osm_xml)
    )
    # meta_data_list = json_normalize(meta_data_list)

    if True:  # Add keys if missing, for tabular repr
        exclude_keys = ("geometry",)
        str_transform_keys = ("osmid",)

        all_line_keys = set()
        for line in lines_meta_data:
            for k in line.keys():
                if k not in exclude_keys:
                    all_line_keys.add(k)

        for i, l in enumerate(lines_meta_data):
            for exclude_key in exclude_keys:
                if exclude_key in l:
                    lines_meta_data[i].pop(exclude_key)

            for s in str_transform_keys:
                if s in l:
                    lines_meta_data[i][s] = str(lines_meta_data[i][s])

            for a in all_line_keys:
                if a not in lines_meta_data[i]:
                    lines_meta_data[i][a] = None

    if True:  # Add keys if missing, for tabular repr
        exclude_keys = ("geometry",)
        str_transform_keys = ("osmid",)

        all_point_keys = set()
        for point in points_meta_data:
            for k in point.keys():
                all_point_keys.add(k)

        for i, l in enumerate(points_meta_data):
            for exclude_key in exclude_keys:
                if exclude_key in l:
                    points_meta_data[i].pop(exclude_key)

            for s in str_transform_keys:
                if s in l:
                    points_meta_data[i][s] = str(points_meta_data[i][s])

            for a in all_point_keys:
                if a not in points_meta_data[i]:
                    points_meta_data[i][a] = None

    assert len(lines) == len(lines_meta_data), f"{len(lines)=}{len(lines_meta_data)=}"
    assert len(points) == len(
        points_meta_data
    ), f"{len(points)=}{len(points_meta_data)=}"

    return (lines, lines_meta_data), (points, points_meta_data)
