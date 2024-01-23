from pathlib import Path
from typing import Any, Hashable, Iterator, Mapping, Optional, Sequence, TypeVar

import geopandas
from integration_system.model import Solution
from integration_system.model.mixins import CollectionMixin

from jord.qlive_utilities import add_dataframe_layer, add_shapely_layer
from qgis.core import (
    QgsProject,
)
from warg import ensure_in_sys_path

ensure_in_sys_path(Path(__file__).parent.parent)

from ...configuration.constants import CMS_HIERARCHY_GROUP_NAME


import dataclasses
from pandas import DataFrame, json_normalize


def to_df(coll_mix: CollectionMixin) -> DataFrame:
    return json_normalize(dataclasses.asdict(obj) for obj in coll_mix)


def solution_to_layer_hierarchy(
    qgis_instance_handle: Any,
    solution: Solution,
    venues_map: Mapping,
    venue_name: str,
    cms_hierarchy_group_name: str = CMS_HIERARCHY_GROUP_NAME,
) -> None:
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    cms_group = layer_tree_root.findGroup(cms_hierarchy_group_name)

    if not cms_group:  # add it if it does not exist
        cms_group = layer_tree_root.addGroup(cms_hierarchy_group_name)

    solution_name = f"{solution.name} (Solution)"
    solution_group = layer_tree_root.findGroup(solution_name)
    if not solution_group:
        solution_group = cms_group.insertGroup(0, solution_name)

    venue = None
    for v in solution.venues:
        if v.external_id == venues_map[venue_name]:
            venue = v
            break

    venue_group = solution_group.insertGroup(0, f"{venue.name} (Venue)")

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
