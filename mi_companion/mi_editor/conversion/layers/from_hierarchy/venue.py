import copy
import logging
from datetime import datetime
from typing import Any, Callable, List, Mapping, Optional

from PyQt5.QtCore import QDateTime

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.mi import SolutionDepth
from integration_system.model import PostalAddress, Solution, VenueType
from mi_companion import (
    DEFAULT_CUSTOM_PROPERTIES,
    HALF_SIZE,
    VENUE_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
)
from .building import add_venue_level_hierarchy
from .custom_props import extract_custom_props

__all__ = ["convert_solution_venues"]

from .extraction import special_extract_layer_data
from jord.qgis_utilities.conversion.features import feature_to_shapely

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
    progress_bar: Callable,
    solution_external_id: str,
    solution_name: str,
    solution_customer_id: str,
    solution_occupants_enabled: bool,
    ith_solution: int,
    num_solution_elements: int,
    solution_depth: SolutionDepth = SolutionDepth.obstacles,
    include_route_elements: bool = False,
    include_occupants: bool = False,
    include_media: bool = False,
    include_graph: bool = False,
    upload_venues: bool = True,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
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
                external_id=solution_external_id,
                name=solution_name,
                customer_id=solution_customer_id,
                occupants_enabled=solution_occupants_enabled,
                # occupants_enabled =...
                # default_language = ...
            )
        else:
            solution = copy.deepcopy(existing_solution)

        if VENUE_DESCRIPTOR in solution_group_item.name():
            venue_key = get_venue_key(
                solution,
                solution_group_item,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )

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
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )

        post_process_solution(solution)

        if collect_invalid:
            assert upload_venues is False, "Cannot upload venues if collecting invalid"
            title = f"Validation {venue_key}"
            if issues:
                QtWidgets.QMessageBox.information(
                    None, title, "- " + "\n\n- ".join(issues)
                )
            else:
                QtWidgets.QMessageBox.information(None, title, "No issues found")

            issue_points = []
            for issue in issues:
                if isinstance(issue, str):
                    logger.error(issue)
                else:
                    logger.error(f"{issue=}")
                    issue_points.append(issue)

            if issue_points:
                ...
                # qgis_instance_handle.iface.mapCanvas().setSelection(            issue_points            )
                # add_shapely_layer(qgis_instance_handle=qgis_instance_handle, geoms=issue_points)
                # TODO: Add  shapely layer with issues

        elif upload_venues:
            assert (
                len(issues) == 0
                and not collect_invalid
                and not collect_warnings
                and not collect_errors
            ), (
                f"Did not expect issues: {issues=}, {collect_invalid=}, {collect_warnings=}, {collect_errors=}, "
                f"cannot upload!"
            )
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


def get_venue_key(
    solution: Solution,
    venue_group_items: Any,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> Optional[str]:
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

            venue_type = get_venue_type(layer_attributes)

            last_verified = get_last_verified(layer_attributes)

            address = get_address(layer_attributes)

            geom_shapely = feature_to_shapely(layer_feature)
            if geom_shapely:
                custom_props = extract_custom_props(layer_attributes)
                try:
                    venue_key = solution.add_venue(
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
                except Exception as e:
                    _invalid = f"Invalid venue: {e}"
                    logger.error(_invalid)
                    if collect_invalid:
                        issues.append(_invalid)
                        return None
                    else:
                        raise e

                return venue_key

    logger.error(f"Did not find venue in {venue_group_items.children()=}")


def get_address(layer_attributes):
    if "address.city" in layer_attributes and layer_attributes["address.city"]:
        address = PostalAddress(
            city=layer_attributes["address.city"],
            region=layer_attributes["address.region"],
            street1=layer_attributes["address.street1"],
            country=layer_attributes["address.country"],
            street2=layer_attributes["address.street2"],
            postal_code=layer_attributes["address.postal_code"],
        )

    else:
        address = None
    return address


def get_last_verified(layer_attributes: Mapping) -> datetime:
    if "last_verified" in layer_attributes and layer_attributes["last_verified"]:
        last_verified = layer_attributes["last_verified"]

        if isinstance(last_verified, str):
            ...
        elif isinstance(last_verified, QDateTime):
            try:
                last_verified = last_verified.toPyDate()
            except:
                try:
                    last_verified = last_verified.toPyDateTime()
                except:
                    try:
                        last_verified = last_verified.toPython()
                    except Exception as e:
                        raise e

        elif isinstance(last_verified, datetime):
            last_verified = last_verified.timestamp()
        # elif isinstance(last_verified, int):
        #  last_verified = last_verified * 1000
        elif isinstance(last_verified, QVariant):
            # logger.warning(f"{typeToDisplayString(type(v))}")
            if last_verified.isNull():  # isNull(v):
                venue_type_str = None
            else:
                venue_type_str = last_verified.value()

    else:
        last_verified = None

    return last_verified


def get_venue_type(layer_attributes):
    if "venue_type" in layer_attributes and layer_attributes["venue_type"]:
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
    else:
        venue_type = VenueType.not_specified
    return venue_type
