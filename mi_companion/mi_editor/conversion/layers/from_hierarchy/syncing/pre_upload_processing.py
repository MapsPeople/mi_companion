import logging
from collections import defaultdict
from itertools import chain

import shapely
from jord.shapely_utilities import is_multi

from integration_system.model import Room, Area
from mi_companion.configuration.options import read_bool_setting

logger = logging.getLogger(__name__)


def post_process_solution(solution):
    floor_child_geoms = defaultdict(list)
    floor_child_geoms_extras = defaultdict(list)
    for floor in solution.floors:
        for feat in chain(solution.rooms, solution.areas, solution.points_of_interest):
            assert hasattr(feat, "floor")
            if feat.floor.key == floor.key:
                if isinstance(feat, Room):  #
                    floor_child_geoms[floor.key].append(feat.polygon)
                    floor_child_geoms_extras[floor.key].append(feat.polygon)
                elif isinstance(feat, Area):  #
                    floor_child_geoms_extras[floor.key].append(feat.polygon)
                else:
                    floor_child_geoms_extras[floor.key].append(feat.point)  # POI

    building_floor_polygons = defaultdict(list)
    building_floor_extras = defaultdict(list)
    for building in solution.buildings:
        for floor in solution.floors:
            if floor.building.key == building.key:
                building_floor_polygons[building.key].append(floor.polygon)
                # EXTRAS FOR LATER USE IN HIERARCHY
                building_floor_extras[building.key].append(floor.polygon)
                building_floor_extras[building.key].extend(floor_child_geoms[floor.key])
                building_floor_extras[building.key].extend(
                    floor_child_geoms_extras[floor.key]
                )

    venue_building_polygons = defaultdict(list)
    venue_building_extras = defaultdict(list)
    for venue in solution.venues:
        for building in solution.buildings:
            if building.venue.key == venue.key:
                venue_building_polygons[venue.key].append(building.polygon)
                # EXTRAS FOR LATER USE IN HIERARCHY
                venue_building_extras[venue.key].append(building.polygon)
                venue_building_extras[venue.key].extend(
                    building_floor_polygons[building.key]
                )
                venue_building_extras[venue.key].extend(
                    building_floor_extras[building.key]
                )

    if read_bool_setting("POST_FIT_FLOORS"):
        logger.warning(f"Post fitting floors")
        if False:
            logger.error(floor_child_geoms)

        for f_id, f_polys in floor_child_geoms.items():
            new_floor_poly = shapely.unary_union(f_polys)
            if is_multi(new_floor_poly):
                logger.error(new_floor_poly)
                logger.error(f_polys)
                logger.error(
                    f"Building {f_id}, {new_floor_poly=} and thus not valid, skipping fit"
                )
                continue
            solution.update_floor(f_id, polygon=new_floor_poly)

    if read_bool_setting("POST_FIT_BUILDINGS"):
        logger.warning(f"Post fitting buildings")
        if False:
            logger.error(building_floor_polygons)

        for b_id, b_f_polys in building_floor_polygons.items():
            new_building_poly = shapely.unary_union(b_f_polys)
            if False:  # INCLUDE ALL FLOOR_GEOM not just "Floor outline"
                new_building_poly = shapely.unary_union(
                    (new_building_poly, *building_floor_extras[b_id])
                )

            if is_multi(new_building_poly):
                logger.error(new_building_poly)
                # logger.error(b_f_polys)
                logger.error(
                    f"Building {b_id}, {new_building_poly=} and thus not valid, skipping fit"
                )
                continue
            solution.update_building(b_id, polygon=new_building_poly)

    if read_bool_setting("POST_FIT_VENUES"):
        logger.warning(f"Post fitting venues")
        if False:
            logger.error(venue_building_polygons)

        for v_id, v_b_polys in venue_building_polygons.items():
            new_venue_poly = shapely.unary_union(v_b_polys)

            if True:  # INCLUDE ALL FLOOR_GEOM not just "Building outline"
                new_venue_poly = shapely.unary_union(
                    (new_venue_poly, *venue_building_extras[v_id])
                )

            if False:
                if is_multi(new_venue_poly):
                    logger.error(new_venue_poly)
                    # logger.error(v_b_polys)
                    logger.error(
                        f"Venue {v_id}, {new_venue_poly=} and thus not valid, skipping fit"
                    )
                    continue

            # new_venue_poly = shapely.concave_hull(new_venue_poly)
            new_venue_poly = shapely.concave_hull(new_venue_poly)

            solution.update_venue(v_id, polygon=new_venue_poly)
