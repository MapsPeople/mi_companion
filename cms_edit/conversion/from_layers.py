import shapely
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.cms import SyncLevel, get_cms_solution, synchronize
from integration_system.cms.config import get_settings, Settings
from integration_system.model import Solution

__all__ = ["layer_hierarchy_to_solution"]

from ...configuration.constants import (
    POINT_INSIDE_MAPS_INDOORS_CUSTOMER_ID,
    VERBOSE,
    CMS_HIERARCHY_GROUP_NAME,
)


def layer_hierarchy_to_solution(
    cms_hierarchy_group_name: str = CMS_HIERARCHY_GROUP_NAME,
    customer_id: str = POINT_INSIDE_MAPS_INDOORS_CUSTOMER_ID,
    *,
    settings: Settings = get_settings(),
) -> None:
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    cms_group = layer_tree_root.findGroup(cms_hierarchy_group_name)

    if not cms_group:  # did not find the group
        return

    for solution_group_items in cms_group.children():
        if isinstance(solution_group_items, QgsLayerTreeGroup):
            solution_name = str(solution_group_items.name()).strip("(Solution)").strip()
            solution = Solution(solution_name, solution_name, customer_id)
            print(f"Converting {str(solution_group_items.name())}")
            for venue_group_items in solution_group_items.children():
                venue_key = None
                for building_group_items in venue_group_items.children():
                    if (
                        isinstance(building_group_items, QgsLayerTreeLayer)
                        and "venue" in building_group_items.name()
                        and venue_key is None
                    ):
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
                            shapely.from_wkt(venue_feature.geometry().asWkt()).simplify(
                                0
                            ),
                        )
                assert venue_key, venue_key

                for building_group_items in venue_group_items.children():
                    if isinstance(building_group_items, QgsLayerTreeGroup):
                        building_key = None
                        for floor_group_items in building_group_items.children():
                            if (
                                isinstance(floor_group_items, QgsLayerTreeLayer)
                                and "building" in floor_group_items.name()
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
                                    ).simplify(0),
                                    venue_key=venue_key,
                                )
                        assert building_key, building_key
                        for floor_group_items in building_group_items.children():
                            if isinstance(floor_group_items, QgsLayerTreeGroup):
                                floor_key = None
                                for (
                                    inventory_group_items
                                ) in floor_group_items.children():
                                    if (
                                        isinstance(
                                            inventory_group_items, QgsLayerTreeLayer
                                        )
                                        and "floor" in inventory_group_items.name()
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
                                            ).simplify(0),
                                            building_key=building_key,
                                        )
                                assert floor_key, floor_key
                                add_floor_inventory(
                                    floor_group_items, floor_key, solution
                                )

            if True:
                if VERBOSE:
                    print("Synchronising")
                existing_solution = get_cms_solution(
                    solution.external_id, settings=settings
                )
                for graph in existing_solution.graphs:
                    solution.add_graph(graph.graph_id, graph.osm_xml)
                synchronize(solution, sync_level=SyncLevel.VENUE, settings=settings)
                if VERBOSE:
                    print("Synchronised")


def add_floor_inventory(
    floor_group_items: QgsLayerTreeGroup, floor_key: str, solution: Solution
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

                room_key = solution.add_room(
                    room_attributes["external_id"],
                    room_attributes["name"],
                    shapely.from_wkt(room_feature.geometry().asWkt()).simplify(0),
                    floor_key=floor_key,
                    location_type_key=room_attributes["location_type.name"],
                )
                if VERBOSE:
                    print("added room", room_key)

        if (
            isinstance(inventory_group_items, QgsLayerTreeLayer)
            and "doors" in inventory_group_items.name()
            and floor_key is not None
            and False  # DISABLED FOR NOW
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
                    linestring=shapely.from_wkt(
                        door_feature.geometry().asWkt()
                    ).simplify(0),
                    door_type=door_attributes["door_type"],
                    floor_key=floor_key,
                )
                if VERBOSE:
                    print("added door", door_key)

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

                poi_key = solution.add_point_of_interest(
                    poi_attributes["external_id"],
                    name=poi_attributes["external_id"],
                    point=shapely.from_wkt(poi_feature.geometry().asWkt()).simplify(0),
                    floor_key=floor_key,
                    location_type_key=poi_attributes["location_type.name"],
                )
                if VERBOSE:
                    print("added poi", poi_key)

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

                area_key = solution.add_area(
                    area_attributes["external_id"],
                    name=area_attributes["external_id"],
                    polygon=shapely.from_wkt(area_feature.geometry().asWkt()).simplify(
                        0
                    ),
                    floor_key=floor_key,
                    location_type_key=area_attributes["location_type.name"],
                )

                if VERBOSE:
                    print("added area", area_key)
