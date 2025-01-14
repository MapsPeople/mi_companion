import logging
from typing import Any, List, Optional

from jord.qgis_utilities.conversion.features import feature_to_shapely

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.mi import (
    MI_OUTSIDE_BUILDING_NAME,
    get_outside_building_floor_name,
)
from integration_system.model import Solution
from mi_companion import (
    BUILDING_POLYGON_DESCRIPTOR,
    DEFAULT_CUSTOM_PROPERTIES,
    FLOOR_DESCRIPTOR,
    GRAPH_DESCRIPTOR,
    HALF_SIZE,
    HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS,
)
from .custom_props import extract_custom_props
from .extraction import special_extract_layer_data
from .floor import add_building_floors
from .graph import add_venue_graph
from .location import add_floor_contents
from ...projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)

__all__ = ["add_venue_level_hierarchy"]


def add_venue_level_hierarchy(
    *,
    ith_solution: int,
    ith_venue: int,
    num_solution_elements: int,
    num_venue_elements: int,
    progress_bar: Optional[Any],
    solution: Solution,
    solution_group_item: Any,
    venue_key: str,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    venue_group_elements = solution_group_item.children()
    num_venue_group_elements = len(venue_group_elements)
    for ith_venue_group_item, venue_group_item in enumerate(venue_group_elements):
        if progress_bar:
            progress_bar.setValue(
                int(
                    10
                    + (
                        90
                        * ((ith_solution + HALF_SIZE) / num_solution_elements)
                        * ((ith_venue + HALF_SIZE) / num_venue_elements)
                        * (
                            (ith_venue_group_item + HALF_SIZE)
                            / num_venue_group_elements
                        )
                    )
                )
            )

        if not isinstance(venue_group_item, QgsLayerTreeGroup):
            logger.debug(f"skipping {venue_group_item=}")
        else:
            if (
                HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS
                and FLOOR_DESCRIPTOR in venue_group_item.name()
                and "Outside" in venue_group_item.name()
            ):  # HANDLE OUTSIDE FLOORS, TODO: right now only support a single floor
                logger.error("Adding outside floor")
                outside_building_admin_id = f"_{venue_key}"
                outside_building = solution.buildings.get(outside_building_admin_id)
                venue = solution.venues.get(venue_key)

                if outside_building is None:
                    try:
                        outside_building_key = solution.add_building(
                            outside_building_admin_id,
                            MI_OUTSIDE_BUILDING_NAME,
                            polygon=venue.polygon,
                            venue_key=venue_key,
                        )
                    except Exception as e:
                        _invalid = f"Error adding outside building: {e}"

                        logger.error(_invalid)

                        if collect_invalid:
                            issues.append(_invalid)
                            continue
                        else:
                            raise e
                else:
                    outside_building_key = outside_building.key

                try:
                    outside_floor_key = solution.add_floor(
                        0,
                        name=get_outside_building_floor_name(0),
                        building_key=outside_building_key,
                        polygon=venue.polygon,
                    )
                except Exception as e:
                    _invalid = f"Error adding outside floor: {e}"

                    logger.error(_invalid)

                    if collect_invalid:
                        issues.append(_invalid)
                        continue
                    else:
                        raise e

                add_floor_contents(
                    floor_key=outside_floor_key,
                    floor_group_items=venue_group_item,
                    solution=solution,
                    issues=issues,
                    collect_invalid=collect_invalid,
                    collect_warnings=collect_warnings,
                    collect_errors=collect_errors,
                )
            else:
                building_key = get_building_key(
                    venue_group_item,
                    solution,
                    venue_key,
                    issues=issues,
                    collect_invalid=collect_invalid,
                    collect_warnings=collect_warnings,
                    collect_errors=collect_errors,
                )

                if building_key is None:
                    logger.error(
                        f"did not find building in {venue_group_item.name()}, skipping"
                    )
                else:
                    add_building_floors(
                        building_key=building_key,
                        venue_group_item=venue_group_item,
                        solution=solution,
                        progress_bar=progress_bar,
                        ith_solution=ith_solution,
                        ith_venue=ith_venue,
                        ith_building=ith_venue_group_item,
                        num_solution_elements=num_solution_elements,
                        num_venue_elements=num_venue_elements,
                        num_building_elements=num_venue_group_elements,
                        issues=issues,
                        collect_invalid=collect_invalid,
                        collect_warnings=collect_warnings,
                        collect_errors=collect_errors,
                    )

    for ith_venue_group_item, venue_group_item in enumerate(venue_group_elements):
        if progress_bar:
            progress_bar.setValue(
                int(
                    10
                    + (
                        90
                        * ((ith_solution + HALF_SIZE) / num_solution_elements)
                        * ((ith_venue + HALF_SIZE) / num_venue_elements)
                        * (
                            (ith_venue_group_item + HALF_SIZE)
                            / num_venue_group_elements
                        )
                    )
                )
            )

        if not isinstance(venue_group_item, QgsLayerTreeGroup):
            logger.debug(f"skipping {venue_group_item=}")
        else:
            if GRAPH_DESCRIPTOR in venue_group_item.name():
                graph_key = add_venue_graph(
                    solution=solution,
                    graph_group=venue_group_item,
                    issues=issues,
                    collect_invalid=collect_invalid,
                    collect_warnings=collect_warnings,
                    collect_errors=collect_errors,
                )

                if graph_key:
                    venue = solution.venues.get(venue_key)
                    venue.graph = solution.graphs.get(graph_key)


def get_building_key(
    building_group_items: Any,
    solution: Solution,
    venue_key: str,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> Optional[str]:
    for floor_group_items in building_group_items.children():
        if (
            isinstance(floor_group_items, QgsLayerTreeLayer)
            and BUILDING_POLYGON_DESCRIPTOR.lower().strip()
            in str(floor_group_items.name()).lower().strip()
        ):
            (
                admin_id,
                external_id,
                layer_attributes,
                layer_feature,
                name,
            ) = special_extract_layer_data(floor_group_items)

            door_linestring = feature_to_shapely(layer_feature)

            if door_linestring is not None:
                custom_props = extract_custom_props(layer_attributes)
                try:
                    building_key = solution.add_building(
                        admin_id=admin_id,
                        external_id=external_id,
                        name=name,
                        polygon=prepare_geom_for_mi_db(door_linestring),
                        venue_key=venue_key,
                        custom_properties=(
                            custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                        ),
                    )
                except Exception as e:
                    _invalid = f"Invalid building: {e}"
                    logger.error(_invalid)
                    if collect_invalid:
                        issues.append(_invalid)
                        return None
                    else:
                        raise e

                return building_key
