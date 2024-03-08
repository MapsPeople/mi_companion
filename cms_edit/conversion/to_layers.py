import dataclasses
import logging
from pathlib import Path
from typing import Any, Optional
from xml.etree.ElementTree import ParseError

import geopandas
import shapely
from jord.qlive_utilities import add_dataframe_layer, add_shapely_layer
from pandas import DataFrame, json_normalize
from qgis.PyQt import QtWidgets
from qgis.core import QgsProject
from warg import ensure_in_sys_path

from integration_system.mi import get_remote_solution
from integration_system.mi.config import Settings, get_settings
from integration_system.model.mixins import CollectionMixin
from .graph.to_lines import osm_xml_to_lines

ensure_in_sys_path(Path(__file__).parent.parent)

from ...configuration.constants import (
    CMS_HIERARCHY_GROUP_NAME,
    SOLUTION_DESCRIPTOR,
    FLOOR_DESCRIPTOR,
    BUILDING_DESCRIPTOR,
    VENUE_DESCRIPTOR,
    SOLUTION_DATA_DESCRIPTOR,
    FLOOR_POLYGON_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
    NAVIGATION_LINES_DESCRIPTOR,
    NAVIGATION_POINT_DESCRIPTOR,
    ADD_GRAPH,
    ONLY_SHOW_FIRST_FLOOR,
)


__all__ = ["solution_to_layer_hierarchy"]


logger = logging.getLogger(__name__)


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
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
) -> None:
    if progress_bar:
        progress_bar.setValue(0)
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    solution = get_remote_solution(
        solution_external_id, [venue_external_id], settings=settings
    )

    cms_group = layer_tree_root.findGroup(cms_hierarchy_group_name)

    if not cms_group:  # add it if it does not exist
        cms_group = layer_tree_root.addGroup(cms_hierarchy_group_name)

    cms_group.setExpanded(True)
    # cms_group.setExpanded(False)

    solution_name = f"{solution.name} {SOLUTION_DESCRIPTOR}"
    solution_group = layer_tree_root.findGroup(solution_name)
    if not solution_group:
        solution_group = cms_group.insertGroup(0, solution_name)

    solution_group.setExpanded(True)
    # solution_group.setExpanded(False)

    venue = None
    for v in solution.venues:
        if v.external_id == venue_external_id:
            venue = v
            break

    # solution_layer_name = f"{solution.name}_solution_data"
    # solution_data_layers = QgsProject.instance().mapLayersByName(solution_layer_name)
    # logger.info(f"Found {solution_data_layers}")
    found_solution_data = False
    # found_solution_data = len(solution_data_layers)>0
    for c in solution_group.children():
        if SOLUTION_DATA_DESCRIPTOR in c.name():
            found_solution_data = True

    if not found_solution_data:
        if venue:
            solution_point = venue.polygon.representative_point()
        else:
            solution_point = shapely.Point(0, 0)

        add_shapely_layer(
            qgis_instance_handle=qgis_instance_handle,
            name=SOLUTION_DATA_DESCRIPTOR,
            group=solution_group,
            geoms=[solution_point],  # Does not really matter where this point is
            columns=[
                {
                    "external_id": solution.external_id,
                    "name": solution.name,
                    "customer_id": solution.customer_id,
                    "occupants_enabled": solution.occupants_enabled,
                }
            ],
            visible=False,
        )

    if venue is None:
        logger.warning("Venue was not found!")
        return
    if progress_bar:
        progress_bar.setValue(10)

    venue_name = f"{venue.name} {VENUE_DESCRIPTOR}"
    venue_group = solution_group.findGroup(venue_name)
    if venue_group:
        logger.warning("Venue already loaded!")
        return

    venue_group = solution_group.insertGroup(0, venue_name)
    venue_group.setExpanded(True)
    venue_group.setExpanded(False)

    if ADD_GRAPH:  # add graph
        try:
            (lines, lines_meta_data), (points, points_meta_data) = osm_xml_to_lines(
                venue.graph.osm_xml
            )
            add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=lines,
                name=NAVIGATION_LINES_DESCRIPTOR,
                group=venue_group,
                columns=lines_meta_data,
                visible=False,
            )

            if True:  # SHOW POINTs AS WELL
                add_shapely_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    geoms=points,
                    name=NAVIGATION_POINT_DESCRIPTOR,
                    group=venue_group,
                    columns=points_meta_data,
                    visible=False,
                )

        except ParseError as e:
            logger.error(e)

    add_shapely_layer(
        qgis_instance_handle=qgis_instance_handle,
        geoms=[venue.polygon],
        name=VENUE_POLYGON_DESCRIPTOR,
        columns=[{"external_id": venue.external_id, "name": venue.name}],
        group=venue_group,
        visible=False,
    )

    if progress_bar:
        progress_bar.setValue(20)

    num_buildings = float(len(solution.buildings))

    for ith, building in enumerate(solution.buildings):
        if progress_bar:
            progress_bar.setValue(int(20 + (float(ith) / num_buildings) * 80))

        if building.venue.external_id == venue.external_id:
            building_group = venue_group.insertGroup(
                0, f"{building.name} {BUILDING_DESCRIPTOR}"
            )
            building_group.setExpanded(True)
            building_group.setExpanded(False)

            add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                geoms=[building.polygon],
                name=BUILDING_POLYGON_DESCRIPTOR,
                columns=[{"external_id": building.external_id, "name": building.name}],
                group=building_group,
                visible=False,
            )

            building_bottom_floor_tracker = {}
            for floor in solution.floors:
                if floor.building.external_id == building.external_id:
                    floor_name = f"{floor.name} {FLOOR_DESCRIPTOR}"
                    floor_group = building_group.insertGroup(
                        0, floor_name
                    )  # MutuallyExclusive = True # TODO: Maybe only show on floor at a time?
                    floor_group.setExpanded(True)
                    floor_group.setExpanded(False)

                    if (
                        ONLY_SHOW_FIRST_FLOOR
                    ):  # Only make first floor of building visible
                        if (
                            building_group.name in building_bottom_floor_tracker
                        ):  # TODO: IMPLEMENT PROPER COMPARISON
                            layer_tree_root.findGroup(
                                floor_name
                            ).setItemVisibilityChecked(False)
                        else:
                            building_bottom_floor_tracker[building_group.name] = (
                                floor.floor_index
                            )

                    add_shapely_layer(
                        qgis_instance_handle=qgis_instance_handle,
                        geoms=[floor.polygon],
                        name=FLOOR_POLYGON_DESCRIPTOR,
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

                    if ADD_GRAPH:
                        doors = to_df(solution.doors)
                        if not doors.empty:
                            doors = doors[
                                doors["door.floor_index"] == floor.floor_index
                                and doors["door.graph_id"] == venue.graph.graph_id
                            ]
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
    return solution
