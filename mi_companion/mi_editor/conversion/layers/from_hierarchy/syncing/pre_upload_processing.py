import logging
from collections import defaultdict
from itertools import chain

import shapely
from jord.qgis_utilities import read_plugin_setting
from jord.shapely_utilities import is_multi

from integration_system.model import Room, Area
from mi_companion import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME

logger = logging.getLogger(__name__)


def post_process_solution(solution):
    floor_child_geoms = defaultdict(list)
    for floor in solution.floors:
        for feat in chain(solution.rooms, solution.areas, solution.points_of_interest):
            assert hasattr(feat, "floor")
            if feat.floor.key == floor.key:
                if isinstance(feat, (Room, Area)):  #
                    floor_child_geoms[floor.key].append(feat.polygon)
                else:
                    floor_child_geoms[floor.key].append(feat.point)  # POI

    building_floor_polygons = defaultdict(list)
    building_floor_extras = defaultdict(list)
    for building in solution.buildings:
        for floor in solution.floors:
            if floor.building.key == building.key:
                building_floor_polygons[building.key].append(floor.polygon)
                building_floor_extras[building.key].extend(floor_child_geoms[floor.key])

    venue_building_polygons = defaultdict(list)
    for venue in solution.venues:
        for building in solution.buildings:
            if building.venue.key == venue.key:
                venue_building_polygons[venue.key].append(building.polygon)
                venue_building_polygons[venue.key].extend(
                    building_floor_polygons[building.key]
                )
                venue_building_polygons[venue.key].extend(
                    building_floor_extras[building.key]
                )

    if read_plugin_setting(
        "POST_FIT_FLOORS",
        default_value=DEFAULT_PLUGIN_SETTINGS["POST_FIT_FLOORS"],
        project_name=PROJECT_NAME,
    ):
        for f_id, f_polys in floor_child_geoms.items():
            new_poly = shapely.unary_union(f_polys)
            if is_multi(new_poly):
                logger.error(
                    f"Building {f_id}, {new_poly=} and thus not valid, skipping fits"
                )
                continue
            solution.update_floor(f_id, polygon=new_poly)

    if read_plugin_setting(
        "POST_FIT_BUILDINGS",
        default_value=DEFAULT_PLUGIN_SETTINGS["POST_FIT_BUILDINGS"],
        project_name=PROJECT_NAME,
    ):
        for b_id, b_f_polys in building_floor_polygons.items():
            new_poly = shapely.unary_union(b_f_polys)
            if read_plugin_setting(
                "POST_FIT_BUILDINGS_TO_ALL_FLOOR_GEOMS",
                default_value=DEFAULT_PLUGIN_SETTINGS[
                    "POST_FIT_BUILDINGS_TO_ALL_FLOOR_GEOMS"
                ],
                project_name=PROJECT_NAME,
            ):  # INCLUDE ALL FLOOR_GEOM not just "FLoor outline"
                new_poly = shapely.unary_union((new_poly, *building_floor_extras[b_id]))

            if is_multi(new_poly):
                logger.error(
                    f"Building {b_id}, {new_poly=} and thus not valid, skipping fits"
                )
                continue
            solution.update_building(b_id, polygon=new_poly)

    if read_plugin_setting(
        "POST_FIT_VENUES",
        default_value=DEFAULT_PLUGIN_SETTINGS["POST_FIT_VENUES"],
        project_name=PROJECT_NAME,
    ):
        for v_id, v_b_polys in venue_building_polygons.items():
            new_poly = shapely.unary_union(v_b_polys)
            if is_multi(new_poly):
                logger.error(
                    f"Venue {v_id}, {new_poly=} and thus not valid, skipping fits"
                )
                continue
            solution.update_venue(v_id, polygon=new_poly)
