import copy
import logging
from typing import Optional

import shapely
from jord.shapely_utilities.base import clean_shape

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.mi.config import Settings
from integration_system.mi.configuration import SolutionDepth
from integration_system.model import Solution
from mi_companion.configuration.constants import (
    VENUE_POLYGON_DESCRIPTOR,
    HALF_SIZE,
    DEFAULT_CUSTOM_PROPERTIES,
)
from .building import add_venue_buildings
from .custom_props import extract_custom_props

__all__ = ["convert_solution_venues"]

from .extraction import extract_layer_data
from .syncing import sync_build_venue_solution
from ...projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets, QtCore

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)


def convert_solution_venues(
    qgis_instance_handle,
    *,
    mi_group_child: QgsLayerTreeGroup,
    existing_solution: Solution,
    progress_bar: callable,
    solution_external_id: str,
    solution_name: str,
    solution_customer_id: str,
    solution_occupants_enabled: bool,
    settings: Settings,
    ith_solution: int,
    num_solution_elements: int,
    solution_depth=SolutionDepth.LOCATIONS,
    include_route_elements=False,
    include_occupants=False,
    include_media=False,
    include_graph=False,
) -> None:
    solution_group_children = mi_group_child.children()
    num_solution_group_elements = len(solution_group_children)
    for ith_solution_child, solution_group_item in enumerate(solution_group_children):
        if progress_bar:
            progress_bar.setValue(
                int(
                    10
                    + (
                        90
                        * ((ith_solution + HALF_SIZE) / num_solution_elements)
                        * (
                            (ith_solution_child + HALF_SIZE)
                            / num_solution_group_elements
                        )
                    )
                )
            )

        if not isinstance(solution_group_item, QgsLayerTreeGroup):
            continue  # Selected the solution_data object

        if existing_solution is None:
            solution = Solution(
                solution_external_id,
                solution_name,
                solution_customer_id,
                occupants_enabled=solution_occupants_enabled,
            )
        else:
            solution = copy.deepcopy(existing_solution)

        venue_key = get_venue_key(solution, solution_group_item)

        if venue_key is None:
            logger.warning(f"Did not find venue for {solution_group_item=}, skipping")
            continue

        add_venue_buildings(
            ith_solution=ith_solution,
            ith_venue=ith_solution_child,
            num_solution_elements=num_solution_elements,
            num_venue_elements=num_solution_group_elements,
            progress_bar=progress_bar,
            solution=solution,
            solution_group_item=solution_group_item,
            venue_key=venue_key,
        )

        sync_build_venue_solution(
            qgis_instance_handle,
            include_graph,
            include_media,
            include_occupants,
            include_route_elements,
            settings,
            solution,
            solution_depth,
            solution_name,
            progress_bar,
        )


def get_venue_key(solution, venue_group_items) -> Optional[str]:
    for venue_level_item in venue_group_items.children():
        layer_type_test = isinstance(venue_level_item, QgsLayerTreeLayer)
        layer_name = str(venue_level_item.name()).lower().strip()
        layer_descriptor_test = VENUE_POLYGON_DESCRIPTOR.lower().strip() in layer_name

        if layer_type_test and layer_descriptor_test:
            external_id, layer_attributes, layer_feature, name = extract_layer_data(
                venue_level_item
            )
            geom_shapely = feature_to_shapely(layer_feature)
            if geom_shapely:
                custom_props = extract_custom_props(layer_attributes)
                return solution.add_venue(
                    external_id=external_id,
                    name=name,
                    polygon=prepare_geom_for_mi_db(geom_shapely),
                    custom_properties=(
                        custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                    ),
                )
    logger.error(f"Did not find venue in {venue_group_items.children()=}")


def feature_to_shapely(layer_feature):
    feature_geom = layer_feature.geometry()
    if feature_geom is not None:
        geom_wkt = feature_geom.asWkt()
        if geom_wkt is not None:
            return shapely.from_wkt(geom_wkt)
