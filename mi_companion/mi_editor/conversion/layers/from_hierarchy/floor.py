import logging

import shapely

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsFeatureRequest,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsProject,
)

from integration_system.model import Solution
from mi_companion.configuration.constants import (
    FLOOR_POLYGON_DESCRIPTOR,
    HALF_SIZE,
)
from .extraction import extract_layer_data
from .location import add_floor_contents
from ...projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)


__all__ = ["add_building_floor"]


def add_building_floor(
    *,
    building_key: str,
    venue_group_item,
    solution: Solution,
    progress_bar,
    ith_solution,
    ith_venue,
    ith_building,
    num_solution_elements,
    num_venue_elements,
    num_building_elements,
) -> None:
    building_group_elements = venue_group_item.children()
    num_building_group_elements = len(building_group_elements)
    for ith_building_group_item, building_group_item in enumerate(
        building_group_elements
    ):
        if progress_bar:
            progress_bar.setValue(
                int(
                    10
                    + (
                        90
                        * ((ith_solution + HALF_SIZE) / num_solution_elements)
                        * ((ith_venue + HALF_SIZE) / num_venue_elements)
                        * ((ith_building + HALF_SIZE) / num_building_elements)
                        * (
                            (ith_building_group_item + HALF_SIZE)
                            / num_building_group_elements
                        )
                    )
                )
            )

        if not isinstance(building_group_item, QgsLayerTreeGroup):
            continue

        floor_attributes, floor_key = get_floor_data(
            building_key, building_group_item, solution
        )

        if floor_key is None:
            logger.error(f"Did not find floor in {building_group_item=}, skipping")
            continue

        add_floor_contents(
            floor_group_items=building_group_item,
            floor_key=floor_key,
            solution=solution,
            graph_key=(
                solution.floors.get(floor_key).building.venue.graph.key
                if solution.floors.get(floor_key).building.venue.graph
                else None
            ),
            floor_index=floor_attributes["floor_index"],
        )


def get_floor_data(building_key, floor_group_items, solution):
    for floor_level_item in floor_group_items.children():
        if (
            isinstance(
                floor_level_item,
                QgsLayerTreeLayer,
            )
            and FLOOR_POLYGON_DESCRIPTOR.lower().strip()
            in str(floor_level_item.name()).lower().strip()
        ):
            external_id, floor_attributes, floor_feature, name = extract_layer_data(
                floor_level_item
            )

            feature_geom = floor_feature.geometry()
            if feature_geom is not None:
                geom_wkt = feature_geom.asWkt()
                if geom_wkt is not None:
                    geom_shapely = shapely.from_wkt(geom_wkt)
                    floor_key = solution.add_floor(
                        external_id=external_id,
                        name=name,
                        floor_index=floor_attributes["floor_index"],
                        polygon=prepare_geom_for_mi_db(geom_shapely),
                        building_key=building_key,
                    )
                    return floor_attributes, floor_key
    return None, None
