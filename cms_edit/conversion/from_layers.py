import copy
import logging
from typing import Optional, Dict

import shapely

from qgis.PyQt import QtWidgets
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.cms import SyncLevel, get_remote_solution, synchronize
from integration_system.cms.config import get_settings, Settings
from integration_system.model import Solution, LocationType

__all__ = ["layer_hierarchy_to_solution"]

from ...configuration.constants import VERBOSE, ALLOW_LOCATION_CREATION, ADD_DOORS


logger = logging.getLogger(__name__)
HALF_SIZE = 0.5

from ...configuration.constants import (
    CMS_HIERARCHY_GROUP_NAME,
    FLOOR_POLYGON_DESCRIPTOR,
    BUILDING_POLYGON_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
    ADD_GRAPH,
)


def layer_hierarchy_to_solution(
    cms_hierarchy_group_name: str = CMS_HIERARCHY_GROUP_NAME,
    *,
    settings: Settings = get_settings(),
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
    iface: Optional[QtWidgets.QWidget] = None,
) -> None:
    if False:
        ...
        # from PyQt6.QtGui import QAction
        # @pyqtSlot(int)
        # def addedGeometry(self, intValue):
        # fun stuff here

        def show_attribute_table(layer) -> None:
            if layer is None:
                layer = iface.activeLayer()
            att_dialog = iface.showAttributeTable(layer)
            # att_dialog.findChild(QAction, "mActionSelectedFilter").trigger()

        from jord.qgis_utilities.helpers import signals

        # signals.reconnect_signal(vlayer.featureAdded, show_attribute_table)
        # for feat in iface.activeLayer().getFeatures():
        #    iface.activeLayer().setSelectedFeatures([feat.id()])

    if progress_bar:
        progress_bar.setValue(0)

    layer_tree_root = QgsProject.instance().layerTreeRoot()

    cms_group = layer_tree_root.findGroup(cms_hierarchy_group_name)

    if not cms_group:  # did not find the group
        return

    if progress_bar:
        progress_bar.setValue(10)

    solution_elements = cms_group.children()
    num_solution_elements = len(solution_elements)
    for ith_solution, solution_group_item in enumerate(solution_elements):
        # TODO: ASSERT SOLUTION_DESCRIPTOR in group name
        if progress_bar:
            progress_bar.setValue(
                int(10 + (90 * (float(ith_solution + 1) / num_solution_elements)))
            )
        if isinstance(solution_group_item, QgsLayerTreeGroup):
            logger.info(f"Serialising {str(solution_group_item.name())}")

            solution_layer_name = (
                str(solution_group_item.name()).split("(Solution)")[0].strip()
            )

            solution_data_layer_name = "solution_data"

            found_solution_data = False
            solution_data_layer: Optional[Dict] = None
            for c in solution_group_item.children():
                if solution_data_layer_name in c.name():
                    assert (
                        found_solution_data == False
                    ), f"Duplicate {solution_data_layer_name=} for {solution_layer_name=}"
                    found_solution_data = True

                    solution_feature = c.layer().getFeature(1)  # 1 is first element
                    solution_data_layer = {
                        k.name(): v
                        for k, v in zip(
                            solution_feature.fields(), solution_feature.attributes()
                        )
                    }

            assert (
                found_solution_data
            ), f"Did not find {solution_data_layer_name=} for {solution_layer_name=}"

            solution_external_id = solution_data_layer["external_id"]
            solution_customer_id = solution_data_layer["customer_id"]
            solution_occupants_enabled = solution_data_layer["occupants_enabled"]
            solution_name = solution_data_layer["name"]

            if solution_external_id is None:
                solution_external_id = solution_name

            existing_solution = get_remote_solution(
                solution_external_id, venue_keys=[], settings=settings
            )

            logger.info(f"Converting {str(solution_group_item.name())}")

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
                print(f"set venue key back to {venue_key=}")
                for building_group_items in venue_group_items.children():
                    layer_type_test = isinstance(
                        building_group_items, QgsLayerTreeLayer
                    )
                    layer_name = str(building_group_items.name()).lower()
                    layer_descriptor_test = (
                        VENUE_POLYGON_DESCRIPTOR.lower() in layer_name
                    )

                    if layer_type_test and layer_descriptor_test:
                        assert venue_key is None, f"{venue_key=} was already set"
                        venue_polygon_layer = building_group_items.layer()
                        venue_feature = venue_polygon_layer.getFeature(
                            1
                        )  # 1 is first element

                        venue_attributes = {
                            k.name(): v
                            for k, v in zip(
                                venue_feature.fields(), venue_feature.attributes()
                            )
                        }
                        venue_key = solution.add_venue(
                            venue_attributes["external_id"],
                            venue_attributes["name"],
                            shapely.from_wkt(venue_feature.geometry().asWkt())
                            .simplify(0)
                            .buffer(0),
                        )
                        print(f"set venue key to {venue_key=}")
                        assert venue_key, f"Returned {venue_key=}"

                assert venue_key, f"Did not find a {venue_key=}"

                building_elements = venue_group_items.children()
                num_building_elements = len(building_elements)
                for ith_building, building_group_items in enumerate(building_elements):
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
                                    * ((ith_venue + HALF_SIZE) / num_venue_elements)
                                    * (
                                        (ith_building + HALF_SIZE)
                                        / num_building_elements
                                    )
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
                                    1
                                )  # 1 is first element

                                building_attributes = {
                                    k.name(): v
                                    for k, v in zip(
                                        building_feature.fields(),
                                        building_feature.attributes(),
                                    )
                                }
                                building_key = solution.add_building(
                                    building_attributes["external_id"],
                                    building_attributes["name"],
                                    shapely.from_wkt(
                                        building_feature.geometry().asWkt()
                                    )
                                    .simplify(0)
                                    .buffer(0),
                                    venue_key=venue_key,
                                )
                        assert building_key, building_key

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
                                            inventory_group_items, QgsLayerTreeLayer
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
                                        floor_key = solution.add_floor(
                                            floor_attributes["external_id"],
                                            floor_attributes["name"],
                                            floor_attributes["floor_index"],
                                            shapely.from_wkt(
                                                floor_feature.geometry().asWkt()
                                            )
                                            .simplify(0)
                                            .buffer(0),
                                            building_key=building_key,
                                        )
                                assert floor_key, floor_key
                                add_floor_inventory(
                                    floor_group_items=floor_group_items,
                                    floor_key=floor_key,
                                    solution=solution,
                                    graph_key=None,  # graph.key,
                                    floor_index=floor_attributes["floor_index"],
                                )

                if False:
                    existing_venue_solution = get_remote_solution(
                        solution_name, venue_keys=[venue_key], settings=settings
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
                                media_key=occupant.logo.key if occupant.logo else None,
                            )

                if VERBOSE:
                    logger.info("Synchronising")

                synchronize(solution, sync_level=SyncLevel.VENUE, settings=settings)

                if VERBOSE:
                    logger.info("Synchronised")


def add_floor_inventory(
    *,
    floor_group_items: QgsLayerTreeGroup,
    floor_key: str,
    graph_key: str,
    solution: Solution,
    floor_index: int,
) -> None:
    for inventory_group_items in floor_group_items.children():
        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and "rooms" in inventory_group_items.name()
            and floor_key is not None
        ):
            room_polygon_layer = inventory_group_items.layer()
            for room_feature in room_polygon_layer.getFeatures():
                room_attributes = {
                    k.name(): v
                    for k, v in zip(
                        room_feature.fields(),
                        room_feature.attributes(),
                    )
                }

                location_type_name = room_attributes["location_type.name"]
                location_type_key = LocationType.compute_key(location_type_name)
                if ALLOW_LOCATION_CREATION:  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                    if solution.location_types.get(location_type_key) is None:
                        location_type_key = solution.add_location_type(
                            location_type_name
                        )

                room_key = solution.add_room(
                    room_attributes["external_id"],
                    room_attributes["name"],
                    shapely.from_wkt(room_feature.geometry().asWkt())
                    .simplify(0)
                    .buffer(0),
                    floor_key=floor_key,
                    location_type_key=location_type_key,
                )
                if VERBOSE:
                    logger.info("added room", room_key)

        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and "doors" in inventory_group_items.name()
            and graph_key is not None
            and ADD_DOORS  # DISABLED FOR NOW
        ):
            doors_linestring_layer = inventory_group_items.layer()
            for door_feature in doors_linestring_layer.getFeatures():
                door_attributes = {
                    k.name(): v
                    for k, v in zip(
                        door_feature.fields(),
                        door_feature.attributes(),
                    )
                }

                door_key = solution.add_door(
                    door_attributes["external_id"],
                    linestring=shapely.from_wkt(door_feature.geometry().asWkt())
                    .simplify(0)
                    .buffer(0),
                    door_type=door_attributes["door_type"],
                    floor_index=floor_index,
                    graph_key=graph_key,
                )
                if VERBOSE:
                    logger.info("added door", door_key)

        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and "pois" in inventory_group_items.name()
            and floor_key is not None
        ):
            poi_point_layer = inventory_group_items.layer()
            for poi_feature in poi_point_layer.getFeatures():
                poi_attributes = {
                    k.name(): v
                    for k, v in zip(
                        poi_feature.fields(),
                        poi_feature.attributes(),
                    )
                }

                location_type_name = poi_attributes["location_type.name"]
                location_type_key = LocationType.compute_key(location_type_name)
                if ALLOW_LOCATION_CREATION:  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                    if solution.location_types.get(location_type_key) is None:
                        location_type_key = solution.add_location_type(
                            location_type_name
                        )

                poi_key = solution.add_point_of_interest(
                    poi_attributes["external_id"],
                    name=poi_attributes["external_id"],
                    point=shapely.from_wkt(poi_feature.geometry().asWkt()).simplify(0),
                    floor_key=floor_key,
                    location_type_key=location_type_key,
                )
                if VERBOSE:
                    logger.info("added poi", poi_key)

        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and "areas" in inventory_group_items.name()
            and floor_key is not None
        ):
            doors_linestring_layer = inventory_group_items.layer()
            for area_feature in doors_linestring_layer.getFeatures():
                area_attributes = {
                    k.name(): v
                    for k, v in zip(
                        area_feature.fields(),
                        area_feature.attributes(),
                    )
                }

                location_type_name = area_attributes["location_type.name"]
                location_type_key = LocationType.compute_key(location_type_name)
                if ALLOW_LOCATION_CREATION:  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                    if solution.location_types.get(location_type_key) is None:
                        location_type_key = solution.add_location_type(
                            location_type_name
                        )

                area_key = solution.add_area(
                    area_attributes["external_id"],
                    name=area_attributes["external_id"],
                    polygon=shapely.from_wkt(area_feature.geometry().asWkt())
                    .simplify(0)
                    .buffer(0),
                    floor_key=floor_key,
                    location_type_key=location_type_key,
                )

                if VERBOSE:
                    logger.info("added area", area_key)
