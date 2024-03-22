import copy
import logging
import uuid

import shapely
from jord.shapely_utilities.base import clean_shape

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.mi import SyncLevel, synchronize
from integration_system.model import Solution
from mi_companion.configuration.constants import (
    VERBOSE,
    FLOOR_POLYGON_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
    ADD_GRAPH,
)
from .inventory import add_floor_inventory

__all__ = ["convert_venues"]


logger = logging.getLogger(__name__)
HALF_SIZE = 0.5


GENERATE_MISSING_EXTERNAL_IDS = False


def convert_venues(
    *,
    solution_group_item: QgsLayerTreeGroup,
    existing_solution: Solution,
    progress_bar: callable,
    solution_external_id: str,
    solution_name,
    solution_customer_id,
    solution_occupants_enabled,
    settings,
    ith_solution,
    num_solution_elements,
) -> None:
    venue_elements = solution_group_item.children()
    num_venue_elements = len(venue_elements)
    for ith_venue, venue_group_items in enumerate(venue_elements):
        if not isinstance(venue_group_items, QgsLayerTreeGroup):
            continue  # Selected the solution_data object

        if progress_bar:
            progress_bar.setValue(
                int(
                    10
                    + (
                        90
                        * ((ith_solution + HALF_SIZE) / num_solution_elements)
                        * ((ith_venue + HALF_SIZE) / num_venue_elements)
                    )
                )
            )

        if existing_solution is None:
            solution = Solution(
                solution_external_id,
                solution_name,
                solution_customer_id,
                occupants_enabled=solution_occupants_enabled,
            )
        else:
            solution = copy.deepcopy(existing_solution)

        if ADD_GRAPH:
            for graph in existing_solution.graphs:
                solution.add_graph(graph.graph_id, graph.osm_xml)

        venue_key = None
        for building_group_items in venue_group_items.children():
            layer_type_test = isinstance(building_group_items, QgsLayerTreeLayer)
            layer_name = str(building_group_items.name()).lower()
            layer_descriptor_test = VENUE_POLYGON_DESCRIPTOR.lower() in layer_name

            if layer_type_test and layer_descriptor_test:
                assert venue_key is None, f"{venue_key=} was already set"
                venue_polygon_layer = building_group_items.layer()
                venue_feature = venue_polygon_layer.getFeature(1)  # 1 is first element

                venue_attributes = {
                    k.name(): v
                    for k, v in zip(venue_feature.fields(), venue_feature.attributes())
                }

                if len(venue_attributes) == 0:
                    continue
                else:
                    logger.error(
                        f"Did not find venue, skipping {building_group_items.name()}"
                    )

                external_id = venue_attributes["external_id"]
                if external_id is None:
                    if GENERATE_MISSING_EXTERNAL_IDS:
                        external_id = uuid.uuid4().hex
                    else:
                        raise ValueError(
                            f"{venue_feature} is missing a valid external id"
                        )

                name = venue_attributes["name"]
                if name is None:
                    name = external_id

                venue_key = solution.add_venue(
                    external_id=external_id,
                    name=name,
                    polygon=clean_shape(
                        shapely.from_wkt(venue_feature.geometry().asWkt())
                    ),
                )

        if venue_key:
            building_elements = venue_group_items.children()
            num_building_elements = len(building_elements)
            for ith_building, building_group_items in enumerate(building_elements):
                if progress_bar:
                    progress_bar.setValue(
                        int(
                            10
                            + (
                                90
                                * ((ith_solution + HALF_SIZE) / num_solution_elements)
                                * ((ith_venue + HALF_SIZE) / num_venue_elements)
                                * ((ith_building + HALF_SIZE) / num_building_elements)
                            )
                        )
                    )
                if isinstance(building_group_items, QgsLayerTreeGroup):
                    building_key = None
                    for floor_group_items in building_group_items.children():
                        if (
                            isinstance(floor_group_items, QgsLayerTreeLayer)
                            and BUILDING_POLYGON_DESCRIPTOR.lower()
                            in str(floor_group_items.name()).lower()
                            and venue_key is not None
                            and building_key is None
                        ):
                            building_polygon_layer = floor_group_items.layer()
                            building_feature = building_polygon_layer.getFeature(
                                1  # 1 is the first element
                            )

                            building_attributes = {
                                k.name(): v
                                for k, v in zip(
                                    building_feature.fields(),
                                    building_feature.attributes(),
                                )
                            }

                            if len(building_attributes) == 0:
                                continue
                            else:
                                logger.error(
                                    f"Did not find building, skipping {floor_group_items.name()}"
                                )

                            external_id = building_attributes["external_id"]
                            if external_id is None:
                                if GENERATE_MISSING_EXTERNAL_IDS:
                                    external_id = uuid.uuid4().hex
                                else:
                                    raise ValueError(
                                        f"{building_feature} is missing a valid external id"
                                    )

                            name = building_attributes["name"]
                            if name is None:
                                name = external_id

                            building_key = solution.add_building(
                                external_id=external_id,
                                name=name,
                                polygon=clean_shape(
                                    shapely.from_wkt(
                                        building_feature.geometry().asWkt()
                                    )
                                ),
                                venue_key=venue_key,
                            )
                    if building_key:
                        floor_elements = building_group_items.children()
                        num_floor_elements = len(floor_elements)
                        for ith_floor, floor_group_items in enumerate(floor_elements):
                            if progress_bar:
                                progress_bar.setValue(
                                    int(
                                        10
                                        + (
                                            90
                                            * (
                                                (ith_solution + HALF_SIZE)
                                                / num_solution_elements
                                            )
                                            * (
                                                (ith_venue + HALF_SIZE)
                                                / num_venue_elements
                                            )
                                            * (
                                                (ith_building + HALF_SIZE)
                                                / num_building_elements
                                            )
                                            * (
                                                (ith_floor + HALF_SIZE)
                                                / num_floor_elements
                                            )
                                        )
                                    )
                                )

                            if isinstance(floor_group_items, QgsLayerTreeGroup):
                                floor_key = None
                                for (
                                    inventory_group_items
                                ) in floor_group_items.children():
                                    if (
                                        isinstance(
                                            inventory_group_items,
                                            QgsLayerTreeLayer,
                                        )
                                        and FLOOR_POLYGON_DESCRIPTOR.lower()
                                        in str(inventory_group_items.name()).lower()
                                        and building_key is not None
                                        and floor_key is None
                                    ):
                                        floor_polygon_layer = (
                                            inventory_group_items.layer()
                                        )
                                        floor_feature = floor_polygon_layer.getFeature(
                                            1
                                        )  # 1 is first element

                                        floor_attributes = {
                                            k.name(): v
                                            for k, v in zip(
                                                floor_feature.fields(),
                                                floor_feature.attributes(),
                                            )
                                        }
                                        external_id = floor_attributes["external_id"]
                                        if external_id is None:
                                            if GENERATE_MISSING_EXTERNAL_IDS:
                                                external_id = uuid.uuid4().hex
                                            else:
                                                raise ValueError(
                                                    f"{floor_feature} is missing a valid external id"
                                                )

                                        name = floor_attributes["name"]
                                        if name is None:
                                            name = external_id

                                        floor_key = solution.add_floor(
                                            external_id=external_id,
                                            name=name,
                                            floor_index=floor_attributes["floor_index"],
                                            polygon=clean_shape(
                                                shapely.from_wkt(
                                                    floor_feature.geometry().asWkt()
                                                )
                                            ),
                                            building_key=building_key,
                                        )
                                assert floor_key, floor_key
                                add_floor_inventory(
                                    floor_group_items=floor_group_items,
                                    floor_key=floor_key,
                                    solution=solution,
                                    graph_key=(
                                        solution.floors.get(
                                            floor_key
                                        ).building.venue.graph.key
                                        if solution.floors.get(
                                            floor_key
                                        ).building.venue.graph
                                        else None
                                    ),
                                    floor_index=floor_attributes["floor_index"],
                                )
                    else:
                        logger.error(f"{building_key=}, skipping")

            """if False:
                existing_venue_solution = get_remote_solution(
                    solution_name,
                    venue_keys=[venue_key],
                    settings=settings,
                    only_geodata=True,
                    include_graph=False,
                )
                if existing_venue_solution:
                    for occupant in existing_solution.occupants:
                        solution.add_occupant(
                            location_key=occupant.location.key,
                            occupant_template_key=(
                                occupant.template.key if occupant.template else None
                            ),
                            is_anchor=occupant.is_anchor,
                            is_operating=occupant.is_operating,
                            aliases=occupant.aliases,
                            business_hours=occupant.business_hours,
                            address=occupant.address,
                            contact=occupant.contact,
                            media_key=(occupant.logo.key if occupant.logo else None),
                        )"""
        else:
            f"Did not find a {venue_key=}, skipping"

        if VERBOSE:
            logger.info("Synchronising")

        # TODO: REVISE BUILDING -> VENUE POLYGONS TO FIT FLOOR POLYGONS!
        # WITH UPDATES

        # solution.update_building(key=None,polygon=None)
        # solution.update_venue(key=None,polygon=None)

        synchronize(solution, sync_level=SyncLevel.VENUE, settings=settings)

        if VERBOSE:
            logger.info("Synchronised")
