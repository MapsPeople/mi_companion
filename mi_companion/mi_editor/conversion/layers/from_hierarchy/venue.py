import copy
import logging
from typing import Any, List, Optional

import shapely

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.mi import SolutionDepth
from integration_system.model import PostalAddress, Solution, VenueType
from mi_companion.configuration.constants import (
    DEFAULT_CUSTOM_PROPERTIES,
    HALF_SIZE,
    VENUE_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
)
from .building import add_venue_level_hierarchy
from .custom_props import extract_custom_props

__all__ = ["convert_solution_venues"]

from .extraction import special_extract_layer_data

# from .graph import add_venue_graph
from .syncing import post_process_solution, sync_build_venue_solution
from ...projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets, QtCore

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)


def convert_solution_venues(
    qgis_instance_handle: Any,
    *,
    mi_group_child: QgsLayerTreeGroup,
    existing_solution: Solution,
    progress_bar: callable,
    solution_external_id: str,
    solution_name: str,
    solution_customer_id: str,
    solution_occupants_enabled: bool,
    ith_solution: int,
    num_solution_elements: int,
    solution_depth: SolutionDepth = SolutionDepth.LOCATIONS,
    include_route_elements: bool = False,
    include_occupants: bool = False,
    include_media: bool = False,
    include_graph: bool = False,
    upload_venues: bool = True,
) -> List[Solution]:
    solution_group_children = mi_group_child.children()
    num_solution_group_elements = len(solution_group_children)
    solutions = []
    venue_key = None

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

        if VENUE_DESCRIPTOR in solution_group_item.name():
            venue_key = get_venue_key(solution, solution_group_item)

            if venue_key is None:
                logger.warning(
                    f"Did not find venue for {solution_group_item=}, skipping"
                )
                continue

            add_venue_level_hierarchy(
                ith_solution=ith_solution,
                ith_venue=ith_solution_child,
                num_solution_elements=num_solution_elements,
                num_venue_elements=num_solution_group_elements,
                progress_bar=progress_bar,
                solution=solution,
                solution_group_item=solution_group_item,
                venue_key=venue_key,
            )

        post_process_solution(solution)

        if upload_venues:
            sync_build_venue_solution(
                qgis_instance_handle=qgis_instance_handle,
                include_graph=include_graph,
                include_media=include_media,
                include_occupants=include_occupants,
                include_route_elements=include_route_elements,
                solution=solution,
                solution_depth=solution_depth,
                solution_name=solution_name,
                progress_bar=progress_bar,
            )

        solutions.append(solution)

    return solutions


def get_venue_key(solution: Solution, venue_group_items: Any) -> Optional[str]:
    for venue_level_item in venue_group_items.children():
        layer_type_test = isinstance(venue_level_item, QgsLayerTreeLayer)
        layer_name = str(venue_level_item.name()).lower().strip()
        layer_descriptor_test = VENUE_POLYGON_DESCRIPTOR.lower().strip() in layer_name

        if layer_type_test and layer_descriptor_test:
            (
                admin_id,
                external_id,
                layer_attributes,
                layer_feature,
                name,
            ) = special_extract_layer_data(venue_level_item)

            venue_type_str = layer_attributes["venue_type"]
            if isinstance(venue_type_str, str):
                ...
            elif isinstance(venue_type_str, QVariant):
                # logger.warning(f"{typeToDisplayString(type(v))}")
                if venue_type_str.isNull():  # isNull(v):
                    venue_type_str = None
                else:
                    venue_type_str = venue_type_str.value()

            venue_type = VenueType.__getitem__(venue_type_str)
            last_verified = layer_attributes["last_verified"]

            address = (
                PostalAddress(
                    city=layer_attributes["address.city"],
                    region=layer_attributes["address.region"],
                    street1=layer_attributes["address.street1"],
                    country=layer_attributes["address.country"],
                    street2=layer_attributes["address.street2"],
                    postal_code=layer_attributes["address.postal_code"],
                )
                if "address.city" in layer_attributes
                else None
            )

            geom_shapely = feature_to_shapely(layer_feature)
            if geom_shapely:
                custom_props = extract_custom_props(layer_attributes)
                return solution.add_venue(
                    admin_id=admin_id,
                    external_id=external_id,
                    name=name,
                    polygon=prepare_geom_for_mi_db(geom_shapely),
                    venue_type=venue_type,
                    last_verified=last_verified,
                    custom_properties=(
                        custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                    ),
                    address=address,
                )
    logger.error(f"Did not find venue in {venue_group_items.children()=}")


def feature_to_shapely(layer_feature: Any) -> None:
    feature_geom = layer_feature.geometry()
    if feature_geom is not None:
        geom_wkt = feature_geom.asWkt()
        if geom_wkt is not None:
            return shapely.wkt.loads(geom_wkt)
