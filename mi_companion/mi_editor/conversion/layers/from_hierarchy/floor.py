import logging
import shapely

# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtGui, QtWidgets, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QMessageBox, QTextEdit

# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsFeatureRequest,
    QgsLayerTreeGroup,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsLayerTreeLayer,
    QgsProject,
    QgsProject,
)
from typing import Any, List, Optional, Tuple

from integration_system.model import Solution
from jord.qgis_utilities import (
    extract_field_value,
    feature_to_shapely,
    qgs_geometry_to_shapely,
)
from mi_companion import (
    ANCHOR_AS_INDIVIDUAL_FIELDS,
    HALF_SIZE,
)
from mi_companion.layer_descriptors import FLOOR_POLYGON_DESCRIPTOR
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis
from mi_companion.mi_editor.hierarchy.validation_dialog_utilities import (
    make_hierarchy_validation_dialog,
)
from .common_attributes import extract_translations
from .constants import APPENDIX_INVALID_GEOMETRY_DIALOG_MESSAGE
from .extraction import special_extract_layer_data
from .location import add_floor_contents

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
            reply = make_hierarchy_validation_dialog(
                "Missing Required Floor Polygon Layer",
                f"The Group '{building_group_item.name()}' is missing a {FLOOR_POLYGON_DESCRIPTOR}, which is a "
                f"required layer. If you proceed, the Group '{building_group_item.name()}' will be excluded from "
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
            (admin_id, external_id, floor_attributes, floor_feature) = (
                special_extract_layer_data(floor_level_item)
            )

            floor_polygon = None

            try:
                floor_polygon = feature_to_shapely(floor_feature)
            except Exception as e:
                reply = make_hierarchy_validation_dialog(
                    "Invalid Floor Polygon Detected",
                    f"The Floor Polygon feature with Admin ID '{admin_id}' located in {floor_level_item.name()} has "
                    f"an invalid "
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

            if floor_polygon is None:
                logger.error(f"{floor_polygon=}")

            if floor_polygon is not None:
                translations = extract_translations(floor_attributes)

                anchor = floor_polygon.representative_point()

                if ANCHOR_AS_INDIVIDUAL_FIELDS:
                    if "anchor_x" in floor_attributes:
                        ax = extract_field_value(floor_attributes, "anchor_x")
                        floor_attributes.pop("anchor_x")
                        ay = extract_field_value(floor_attributes, "anchor_y")
                        floor_attributes.pop("anchor_y")
                        anchor = shapely.Point([ax, ay])

                else:

                    if "anchor" in floor_attributes:
                        a = extract_field_value(floor_attributes, "anchor")
                        if a is not None and not (a.isNull() or a.isEmpty()):
                            can = qgs_geometry_to_shapely(a)
                            if can:
                                anchor = can
                        floor_attributes.pop("anchor")

                try:
                    floor_key = solution.add_floor(
                        external_id=external_id,
                        floor_index=floor_attributes["floor_index"],
                        polygon=prepare_geom_for_mi_db_qgis(floor_polygon),
                        building_key=building_key,
                        translations=translations,
                        anchor=prepare_geom_for_mi_db_qgis(anchor),
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

    logger.error(
        f"Did not find floor polygon feature in {floor_group_items.children()=}"
    )
    return None, None
