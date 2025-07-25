import logging
from typing import Any, List, Optional

import shapely

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtGui, QtWidgets, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QMessageBox, QTextEdit

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsLayerTreeGroup,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsLayerTreeLayer,
    QgsProject,
    QgsProject,
)

from jord.qgis_utilities import (
    extract_field_value,
    feature_to_shapely,
    qgs_geometry_to_shapely,
)
from mi_companion import (
    ANCHOR_AS_INDIVIDUAL_FIELDS,
    HALF_SIZE,
    HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS,
)
from mi_companion.layer_descriptors import (
    BUILDING_POLYGON_DESCRIPTOR,
    FLOOR_GROUP_DESCRIPTOR,
    GRAPH_GROUP_DESCRIPTOR,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.routing import (
    add_venue_graph,
)
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis
from mi_companion.mi_editor.hierarchy import (
    make_hierarchy_validation_dialog,
)
from sync_module.mi import (
    MI_OUTSIDE_BUILDING_NAME,
    get_outside_building_floor_name,
)
from sync_module.model import LanguageBundle, Solution
from .common_attributes import extract_translations
from .constants import APPENDIX_INVALID_GEOMETRY_DIALOG_MESSAGE
from .extraction import special_extract_layer_data
from .floor import add_building_floors
from .location import add_floor_contents

logger = logging.getLogger(__name__)

__all__ = ["add_venue_level_hierarchy"]


def add_venue_level_hierarchy(
    *,
    ith_solution: int,
    ith_venue: int,
    num_solution_elements: int,
    num_venue_elements: int,
    progress_bar: Optional[Any],
    solution: Solution,
    solution_group_item: Any,
    venue_key: str,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param ith_solution:
    :param ith_venue:
    :param num_solution_elements:
    :param num_venue_elements:
    :param progress_bar:
    :param solution:
    :param solution_group_item:
    :param venue_key:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
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
            logger.debug(f"skipping {venue_group_item=}")
        elif GRAPH_GROUP_DESCRIPTOR in venue_group_item.name():
            continue
        else:
            if (
                HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS
                and FLOOR_GROUP_DESCRIPTOR in venue_group_item.name()
                and "Outside" in venue_group_item.name()
            ):  # HANDLE OUTSIDE FLOORS, TODO: right now only support a single floor
                logger.error("Adding outside floor")
                outside_building_admin_id = f"_{venue_key}"
                outside_building = solution.buildings.get(outside_building_admin_id)
                venue = solution.venues.get(venue_key)

                if outside_building is None:
                    try:
                        outside_building_key = solution.add_building(
                            admin_id=outside_building_admin_id,
                            translations={
                                "en": LanguageBundle(name=MI_OUTSIDE_BUILDING_NAME)
                            },
                            polygon=venue.polygon,
                            venue_key=venue_key,
                        )
                    except Exception as e:
                        _invalid = f"Error adding outside building: {e}"

                        logger.error(_invalid)

                        if collect_invalid:
                            issues.append(_invalid)
                            continue
                        else:
                            raise e
                else:
                    outside_building_key = outside_building.key

                try:
                    outside_floor_key = solution.add_floor(
                        0,
                        translations={
                            "en": LanguageBundle(
                                name=get_outside_building_floor_name(0)
                            )
                        },
                        building_key=outside_building_key,
                        polygon=venue.polygon,
                    )
                except Exception as e:
                    _invalid = f"Error adding outside floor: {e}"

                    logger.error(_invalid)

                    if collect_invalid:
                        issues.append(_invalid)
                        continue
                    else:
                        raise e

                add_floor_contents(
                    floor_key=outside_floor_key,
                    floor_group_items=venue_group_item,
                    solution=solution,
                    issues=issues,
                    collect_invalid=collect_invalid,
                    collect_warnings=collect_warnings,
                    collect_errors=collect_errors,
                )
            else:
                building_key = get_building_key(
                    venue_group_item,
                    solution,
                    venue_key,
                    issues=issues,
                    collect_invalid=collect_invalid,
                    collect_warnings=collect_warnings,
                    collect_errors=collect_errors,
                )

                if building_key is None:
                    reply = make_hierarchy_validation_dialog(
                        "Missing Required Building Polygon Layer",
                        f"The Group '{venue_group_item.name()}' is missing a {BUILDING_POLYGON_DESCRIPTOR}, "
                        f"which is a "
                        f"required layer. If you proceed, the Group '{venue_group_item.name()}' will be excluded from "
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

                else:
                    add_building_floors(
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
                        issues=issues,
                        collect_invalid=collect_invalid,
                        collect_warnings=collect_warnings,
                        collect_errors=collect_errors,
                    )

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
            logger.debug(f"skipping {venue_group_item=}")
        else:
            if GRAPH_GROUP_DESCRIPTOR in venue_group_item.name():
                graph_key = add_venue_graph(
                    solution=solution,
                    graph_group=venue_group_item,
                    issues=issues,
                    collect_invalid=collect_invalid,
                    collect_warnings=collect_warnings,
                    collect_errors=collect_errors,
                )

                if graph_key:
                    venue = solution.venues.get(venue_key)
                    venue.graph = solution.graphs.get(graph_key)


def get_building_key(
    building_group_items: Any,
    solution: Solution,
    venue_key: str,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> Optional[str]:
    """

    :param building_group_items:
    :param solution:
    :param venue_key:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    for floor_group_items in building_group_items.children():
        if (
            isinstance(floor_group_items, QgsLayerTreeLayer)
            and BUILDING_POLYGON_DESCRIPTOR.lower().strip()
            in str(floor_group_items.name()).lower().strip()
        ):
            (
                admin_id,
                external_id,
                layer_attributes,
                layer_feature,
            ) = special_extract_layer_data(floor_group_items)

            try:
                building_polygon = feature_to_shapely(layer_feature)
            except Exception as e:
                reply = make_hierarchy_validation_dialog(
                    "Invalid Building Polygon Detected",
                    f"The Building Polygon feature with Admin ID '{admin_id}' located in '"
                    f"{floor_group_items.name()}' has an "
                    f"invalid "
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

            if building_polygon is not None:
                translations = extract_translations(layer_attributes)

                anchor = building_polygon.representative_point()

                if ANCHOR_AS_INDIVIDUAL_FIELDS:
                    if "anchor_x" in layer_attributes:
                        ax = extract_field_value(layer_attributes, "anchor_x")
                        layer_attributes.pop("anchor_x")
                        ay = extract_field_value(layer_attributes, "anchor_y")
                        layer_attributes.pop("anchor_y")
                        anchor = shapely.Point([ax, ay])

                else:

                    if "anchor" in layer_attributes:
                        a = extract_field_value(layer_attributes, "anchor")
                        if a is not None and not (a.isNull() or a.isEmpty()):
                            can = qgs_geometry_to_shapely(a)
                            if can:
                                anchor = can
                        layer_attributes.pop("anchor")

                try:
                    building_key = solution.add_building(
                        admin_id=admin_id,
                        external_id=external_id,
                        polygon=prepare_geom_for_mi_db_qgis(building_polygon),
                        venue_key=venue_key,
                        translations=(translations),
                        anchor=prepare_geom_for_mi_db_qgis(anchor),
                    )
                except Exception as e:
                    _invalid = f"Invalid building: {e}"
                    logger.error(_invalid)
                    if collect_invalid:
                        issues.append(_invalid)
                        return None
                    else:
                        raise e

                return building_key

    logger.error(
        f"Did not find building polygon feature in  {building_group_items.children()=}"
    )
    return None
