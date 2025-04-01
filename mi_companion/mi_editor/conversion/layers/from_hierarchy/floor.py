import logging
from typing import Any, List, Optional, Tuple

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsFeatureRequest,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsProject,
)

from integration_system.model import Solution
from jord.qgis_utilities.conversion.features import feature_to_shapely
from mi_companion import DEFAULT_CUSTOM_PROPERTIES, FLOOR_POLYGON_DESCRIPTOR, HALF_SIZE
from .custom_props import extract_custom_props
from .extraction import special_extract_layer_data
from .location import add_floor_contents
from ...projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)

__all__ = ["add_building_floors"]


def add_building_floors(
    *,
    building_key: str,
    venue_group_item: Any,
    solution: Solution,
    progress_bar: Optional[Any],
    ith_solution: int,
    ith_venue: int,
    ith_building: int,
    num_solution_elements: int,
    num_venue_elements: int,
    num_building_elements: int,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param building_key:
    :param venue_group_item:
    :param solution:
    :param progress_bar:
    :param ith_solution:
    :param ith_venue:
    :param ith_building:
    :param num_solution_elements:
    :param num_venue_elements:
    :param num_building_elements:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    building_group_elements = venue_group_item.children()
    num_building_group_elements = len(building_group_elements)

    for ith_building_group_item, building_group_item in enumerate(
        building_group_elements
    ):
        if progress_bar:
            if (
                num_building_elements < 1
                or num_venue_elements < 1
                or num_solution_elements < 1
            ):
                ...
                logger.error(
                    "Come on man... you can not divide by zero... the progress bar was not updated because of you"
                )
            else:
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
            building_key,
            building_group_item,
            solution,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )

        if floor_key is None:
            logger.error(f"Did not find floor in {building_group_item=}, skipping")
            continue

        assert "floor_index" in floor_attributes

        floor_index = floor_attributes["floor_index"]

        add_floor_contents(
            floor_group_items=building_group_item,
            floor_key=floor_key,
            solution=solution,
            graph_key=(
                solution.floors.get(floor_key).building.venue.graph.key
                if solution.floors.get(floor_key).building.venue.graph
                else None
            ),
            floor_index=floor_index,
            issues=issues,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            collect_errors=collect_errors,
        )


def get_floor_data(
    building_key: str,
    floor_group_items: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> Tuple:
    """

    :param building_key:
    :param floor_group_items:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    for floor_level_item in floor_group_items.children():
        if (
            isinstance(
                floor_level_item,
                QgsLayerTreeLayer,
            )
            and FLOOR_POLYGON_DESCRIPTOR.lower().strip()
            in str(floor_level_item.name()).lower().strip()
        ):
            (
                admin_id,
                external_id,
                floor_attributes,
                floor_feature,
                name,
            ) = special_extract_layer_data(floor_level_item)

            door_linestring = feature_to_shapely(floor_feature)

            if door_linestring is None:
                logger.error(f"{door_linestring=}")

            if door_linestring is not None:
                custom_props = extract_custom_props(floor_attributes)

                try:
                    floor_key = solution.add_floor(
                        external_id=external_id,
                        name=name,
                        floor_index=floor_attributes["floor_index"],
                        polygon=prepare_geom_for_mi_db(door_linestring),
                        building_key=building_key,
                        custom_properties=(
                            custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                        ),
                    )
                except Exception as e:
                    _invalid = f"Invalid floor: {e}"
                    logger.error(_invalid)
                    if collect_invalid:
                        issues.append(_invalid)
                        return floor_attributes, None
                    else:
                        raise e

                return floor_attributes, floor_key
    return None, None
