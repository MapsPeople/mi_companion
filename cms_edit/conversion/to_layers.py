from pathlib import Path
from typing import Any

import geopandas
from jord.qlive_utilities import add_dataframe_layer, add_shapely_layer
from qgis.core import (
    QgsProject,
)
from warg import ensure_in_sys_path

from integration_system.cms import get_cms_solution
from integration_system.cms.config import Settings, get_settings
from integration_system.model.mixins import CollectionMixin
from .graph.to_lines import osm_xml_to_lines

ensure_in_sys_path(Path(__file__).parent.parent)

from ...configuration.constants import CMS_HIERARCHY_GROUP_NAME


import dataclasses
from pandas import DataFrame, json_normalize


__all__ = ["solution_to_layer_hierarchy"]


def to_df(coll_mix: CollectionMixin) -> DataFrame:
    # noinspection PyTypeChecker
    return json_normalize(dataclasses.asdict(obj) for obj in coll_mix)


def solution_to_layer_hierarchy(
    qgis_instance_handle: Any,
    solution_external_id: str,
    venue_external_id: str,
    cms_hierarchy_group_name: str = CMS_HIERARCHY_GROUP_NAME,
    *,
    settings: Settings = get_settings(),
) -> None:
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    solution = get_cms_solution(
        solution_external_id, [venue_external_id], settings=settings
    )
    cms_group = layer_tree_root.findGroup(cms_hierarchy_group_name)

    if not cms_group:  # add it if it does not exist
        cms_group = layer_tree_root.addGroup(cms_hierarchy_group_name)

    solution_name = f"{solution.name} (Solution)"
    solution_group = layer_tree_root.findGroup(solution_name)
    if not solution_group:
        solution_group = cms_group.insertGroup(0, solution_name)

    venue = None
    for v in solution.venues:
        if v.external_id == venue_external_id:
            venue = v
            break

    venue_group = solution_group.insertGroup(0, f"{venue.name} (Venue)")

    if False:  # add graph
        (lines, lines_meta_data), (points, points_meta_data) = osm_xml_to_lines(
            venue.graph.osm_xml
        )

        add_shapely_layer(
            qgis_instance_handle=qgis_instance_handle,
            geoms=lines,
            name="navigation_graph_lines",
            group=venue_group,
            columns=lines_meta_data,
        )

        if False:
            add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=points,
                name="navigation_graph_points",
                group=venue_group,
                columns=points_meta_data,
            )

    add_shapely_layer(
        qgis_instance_handle=qgis_instance_handle,
        geoms=[venue.polygon],
        name="venue_polygon",
        columns=[{"external_id": venue.external_id, "name": venue.name}],
        group=venue_group,
        visible=False,
    )

    for building in solution.buildings:
        if building.venue.external_id == venue.external_id:
            building_group = venue_group.insertGroup(0, f"{building.name} (Building)")

            add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[building.polygon],
                name="building_polygon",
                columns=[{"external_id": building.external_id, "name": building.name}],
                group=building_group,
                visible=False,
            )

            for floor in solution.floors:
                if floor.building.external_id == building.external_id:
                    floor_group = building_group.insertGroup(0, f"{floor.name} (Floor)")

                    add_shapely_layer(
                        qgis_instance_handle=qgis_instance_handle,
                        geoms=[floor.polygon],
                        name="floor_polygon",
                        columns=[
                            {
                                "external_id": floor.external_id,
                                "name": floor.name,
                                "floor_index": floor.floor_index,
                            }
                        ],
                        group=floor_group,
                        visible=False,
                    )

                    rooms = to_df(solution.rooms)
                    if not rooms.empty:
                        rooms = rooms[rooms["floor.external_id"] == floor.external_id]
                        rooms_df = geopandas.GeoDataFrame(
                            rooms[
                                [
                                    c
                                    for c in rooms.columns
                                    if ("." not in c) or ("location_type.name" == c)
                                ]
                            ],
                            geometry="polygon",
                        )

                        add_dataframe_layer(
                            qgis_instance_handle=qgis_instance_handle,
                            dataframe=rooms_df,
                            geometry_column="polygon",
                            name="rooms",
                            group=floor_group,
                            categorise_by_attribute="location_type.name",
                        )

                    doors = to_df(solution.doors)
                    if not doors.empty:
                        doors = doors[doors["floor.external_id"] == floor.external_id]
                        door_df = geopandas.GeoDataFrame(
                            doors[[c for c in doors.columns if ("." not in c)]],
                            geometry="linestring",
                        )

                        add_dataframe_layer(
                            qgis_instance_handle=qgis_instance_handle,
                            dataframe=door_df,
                            geometry_column="linestring",
                            name="doors",
                            group=floor_group,
                        )

                    areas = to_df(solution.areas)
                    if not areas.empty:
                        areas = areas[areas["floor.external_id"] == floor.external_id]
                        areas_df = geopandas.GeoDataFrame(
                            areas[
                                [
                                    c
                                    for c in areas.columns
                                    if ("." not in c) or ("location_type.name" == c)
                                ]
                            ],
                            geometry="polygon",
                        )

                        add_dataframe_layer(
                            qgis_instance_handle=qgis_instance_handle,
                            dataframe=areas_df,
                            geometry_column="polygon",
                            name="areas",
                            group=floor_group,
                            categorise_by_attribute="location_type.name",
                        )

                    pois = to_df(solution.points_of_interest)
                    if not pois.empty:
                        pois = pois[pois["floor.external_id"] == floor.external_id]
                        poi_df = geopandas.GeoDataFrame(
                            pois[
                                [
                                    c
                                    for c in pois.columns
                                    if ("." not in c) or ("location_type.name" == c)
                                ]
                            ],
                            geometry="point",
                        )

                        add_dataframe_layer(
                            qgis_instance_handle=qgis_instance_handle,
                            dataframe=poi_df,
                            geometry_column="point",
                            name="pois",
                            group=floor_group,
                            categorise_by_attribute="location_type.name",
                        )
