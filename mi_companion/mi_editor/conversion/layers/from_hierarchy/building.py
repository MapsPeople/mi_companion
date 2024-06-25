import logging
from typing import Any, Optional

import shapely

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import Solution
from mi_companion.configuration.constants import (
    BUILDING_POLYGON_DESCRIPTOR,
    DEFAULT_CUSTOM_PROPERTIES,
    GRAPH_DESCRIPTOR,
    HALF_SIZE,
)
from .custom_props import extract_custom_props
from .extraction import extract_layer_data
from .floor import add_building_floor
from ...projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)

__all__ = ["add_venue_buildings"]


def add_venue_buildings(
    *,
    ith_solution: int,
    ith_venue: int,
    num_solution_elements: int,
    num_venue_elements: int,
    progress_bar: Optional[Any],
    solution: Solution,
    solution_group_item: Any,
    venue_key: str,
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
            continue

        if GRAPH_DESCRIPTOR in venue_group_item.name():
            logger.warning(
                f"Not handling graphs yet, {venue_group_item.name()}, skipping"
            )
            continue

        building_key = get_building_key(venue_group_item, solution, venue_key)

        if building_key is None:
            logger.error(
                f"did not find building in {venue_group_item.name()}, skipping"
            )
            continue

        add_building_floor(
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
        )


def get_building_key(
    building_group_items: Any, solution: Solution, venue_key: str
) -> Optional[str]:
    for floor_group_items in building_group_items.children():
        if (
            isinstance(floor_group_items, QgsLayerTreeLayer)
            and BUILDING_POLYGON_DESCRIPTOR.lower().strip()
            in str(floor_group_items.name()).lower().strip()
        ):
            (
                external_id,
                layer_attributes,
                layer_feature,
                name,
            ) = extract_layer_data(floor_group_items)

            feature_geom = layer_feature.geometry()
            if feature_geom is not None:
                geom_wkt = feature_geom.asWkt()  # TODO: Try asWkb instead
                if geom_wkt is not None:
                    custom_props = extract_custom_props(layer_attributes)
                    geom_shapely = shapely.from_wkt(geom_wkt)  # from wkb instead
                    return solution.add_building(
                        external_id=external_id,
                        name=name,
                        polygon=prepare_geom_for_mi_db(geom_shapely),
                        venue_key=venue_key,
                        custom_properties=(
                            custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                        ),
                    )
