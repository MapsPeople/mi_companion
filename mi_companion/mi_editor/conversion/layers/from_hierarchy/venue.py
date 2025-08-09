import copy
import logging
from datetime import datetime
from typing import Any, Callable, Collection, List, Mapping, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtGui, QtWidgets, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QDateTime, QVariant

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from mi_companion import (
    APPENDIX_INVALID_GEOMETRY_DIALOG_MESSAGE,
    HALF_SIZE,
)
from mi_companion.layer_descriptors import (
    VENUE_GROUP_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
)
from mi_companion.mi_editor.hierarchy.validation_dialog_utilities import (
    make_hierarchy_validation_dialog,
)
from mi_companion.mi_editor.syncing.uploading import upload_venue
from sync_module.mi import SolutionDepth
from sync_module.model import (
    ImplementationStatus,
    OptionalPostalAddress,
    PostalAddress,
    Solution,
)
from sync_module.shared import MIVenueType
from .building import add_venue_level_hierarchy
from mi_companion.qgis_utilities.common_attributes import extract_translations

__all__ = ["convert_solution_venues"]

from mi_companion.qgis_utilities.extraction import special_extract_layer_data
from jord.qgis_utilities import feature_to_shapely

from .location_type import get_location_type_data

# from .graph import add_venue_graph
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis

logger = logging.getLogger(__name__)

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
    solution_available_languages: Collection[str],
    solution_implementation_type: ImplementationStatus,
    solution_default_language: str,
    ith_solution: int,
    num_solution_elements: int,
    solution_depth: SolutionDepth = SolutionDepth.obstacles,
    include_occupants: bool = False,
    include_media: bool = False,
    upload_venues: bool = True,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> List[Solution]:
    """

    :param solution_available_languages:
    :param solution_implementation_type:
    :param solution_default_language:
    :param qgis_instance_handle:
    :param mi_group_child:
    :param existing_solution:
    :param progress_bar:
    :param solution_external_id:
    :param solution_name:
    :param solution_customer_id:
    :param solution_occupants_enabled:
    :param ith_solution:
    :param num_solution_elements:
    :param solution_depth:
    :param include_route_elements:
    :param include_occupants:
    :param include_media:
    :param include_graph:
    :param upload_venues:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    solution_group_children = mi_group_child.children()
    num_solution_group_elements = len(solution_group_children)
    solutions = []
    venue_key = None

    if existing_solution is None:
        solution = Solution(
            _external_id=solution_external_id,
            _name=solution_name,
            _customer_id=solution_customer_id,
        )
    else:
        solution = copy.deepcopy(existing_solution)

    solution.name = solution_name
    solution.customer_id = solution_customer_id
    solution.default_language = solution_default_language
    solution.implementation_type = solution_implementation_type
    solution.occupants_enabled = solution_occupants_enabled
    solution.available_languages = solution_available_languages

    get_location_type_data(solution_group_children, solution)

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

        if VENUE_GROUP_DESCRIPTOR in solution_group_item.name():
            venue_key = get_venue_key(
                solution,
                solution_group_item,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )

            if venue_key is None:
                reply = make_hierarchy_validation_dialog(
                    "Missing Required Venue Polygon Layer",
                    f"The Group '{solution_group_item.name()}' is missing a {VENUE_POLYGON_DESCRIPTOR}, which is a "
                    f"required layer. If you proceed, the Group '{solution_group_item.name()}' will be excluded from "
                    f"the "
                    f"upload.",
                    add_reject_option=True,
                    reject_text="Cancel Upload",
                    accept_text="Upload Anyway",
                    alternative_accept_text="Upload Anyway",
                    level=QtWidgets.QMessageBox.Warning,
                )

                if reply == QMessageBox.RejectRole:
                    raise Exception("Upload cancelled")

                continue
            try:
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
            except Exception as ex:
                logger.error(f"Failed to add {solution_group_item=}, {ex=}")
                QtWidgets.QMessageBox.critical(None, "Error", f"\n\n- {str(ex)}")
                raise ex

        upload_venue(
            collect_errors=collect_errors,
            collect_invalid=collect_invalid,
            collect_warnings=collect_warnings,
            include_media=include_media,
            include_occupants=include_occupants,
            issues=issues,
            progress_bar=progress_bar,
            qgis_instance_handle=qgis_instance_handle,
            solution=solution,
            solution_depth=solution_depth,
            solution_name=solution_name,
            upload_venues=upload_venues,
            venue_key=venue_key,
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
            ) = special_extract_layer_data(venue_level_item)

            try:
                venue_polygon = feature_to_shapely(layer_feature)

            except Exception as e:
                reply = make_hierarchy_validation_dialog(
                    "Invalid Venue Polygon Detected",
                    f"The Venue Polygon feature with Admin ID '{admin_id}' located in '{venue_level_item.name()}' "
                    f"has an invalid "
                    f"geometry.\n\n"
                    # f"\n__________________{e}\n__________________\n"
                    + APPENDIX_INVALID_GEOMETRY_DIALOG_MESSAGE,
                    add_reject_option=True,
                    reject_text="Cancel Upload",
                    accept_text="Upload Anyway",
                    alternative_accept_text="Upload Anyway",
                    level=QtWidgets.QMessageBox.Warning,
                )

                if reply == QMessageBox.RejectRole:
                    raise Exception("Upload cancelled")

            if venue_polygon:
                translations = extract_translations(
                    layer_attributes, required_languages=solution.available_languages
                )
                try:
                    venue_key = solution.add_venue(
                        admin_id=admin_id,
                        external_id=external_id,
                        polygon=prepare_geom_for_mi_db_qgis(venue_polygon),
                        venue_type=get_venue_type(layer_attributes),
                        last_verified=get_last_verified(layer_attributes),
                        translations=translations,
                        address=get_address(layer_attributes),
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
    return None


def get_address(layer_attributes: Mapping[str, Any]) -> OptionalPostalAddress:
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


def get_last_verified(layer_attributes: Mapping[str, Any]) -> Optional[datetime]:
    if "last_verified" in layer_attributes and layer_attributes["last_verified"]:
        last_verified = layer_attributes["last_verified"]

        if isinstance(last_verified, str):
            last_verified = datetime.fromisoformat(last_verified)
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
            ...
            # last_verified = last_verified.timestamp()
        # elif isinstance(last_verified, int):
        #  last_verified = last_verified * 1000
        elif isinstance(last_verified, QVariant):
            # logger.warning(f"{typeToDisplayString(type(v))}")
            if last_verified.isNull():  # isNull(v):
                last_verified = None
            else:
                last_verified = last_verified.value()

    else:
        last_verified = None

    return last_verified


def get_venue_type(layer_attributes: Mapping[str, Any]) -> Optional[MIVenueType]:
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

        # venue_type = VenueType.__getitem__(venue_type_str)
        venue_type = MIVenueType(int(venue_type_str))
    else:
        venue_type = MIVenueType.not_specified

    return venue_type
