import logging
import math
from typing import Any, List, Optional

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer

from integration_system.model import LocationType, Solution
from jord.qgis_utilities import (
    extract_layer_attributes,
)
from warg import str_to_bool
from .common_attributes import extract_display_rule, extract_translations

BOOLEAN_LOCATION_TYPE_ATTRS = ()
STR_LOCATION_TYPE_ATTRS = ("translations.en.name", "admin_id")
FLOAT_LOCATION_TYPE_ATTRS = ()
INTEGER_LOCATION_TYPE_ATTRS = ()

logger = logging.getLogger(__name__)

__all__ = ["get_location_type_data"]


def get_location_type_data(
    solution_group_items: Any,
    solution: Solution,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param solution_group_items:
    :param solution:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    for solution_level_item in solution_group_items:
        if (
            isinstance(
                solution_level_item,
                QgsLayerTreeLayer,
            )
            and "location_types".lower().strip()
            in str(solution_level_item.name()).lower().strip()
        ):
            floor_attributes = extract_layer_attributes(solution_level_item)

            try:

                for attributes in floor_attributes:
                    admin_id = attributes["admin_id"]

                    color = attributes["color"]
                    if color.lower() == "none":
                        color = None

                    is_obstacle = attributes["is_obstacle"]
                    if is_obstacle is None:
                        is_obstacle = None
                    elif not isinstance(is_obstacle, bool):
                        is_obstacle = str_to_bool(is_obstacle)

                    is_selectable = attributes["is_selectable"]
                    if is_selectable is None:
                        is_selectable = None

                    elif not isinstance(is_selectable, bool):
                        is_selectable = str_to_bool(is_selectable)

                    restrictions = attributes["restrictions"]
                    if isinstance(restrictions, bool):  # MAYBE BOOL?
                        logger.error(
                            f"Unexpected type of {restrictions}, should be a list"
                        )
                        restrictions = None

                    elif len(restrictions) == 0:
                        restrictions = None

                    settings_3d_margin = attributes["settings_3d_margin"]
                    if settings_3d_margin == "nan":
                        settings_3d_margin = None
                    else:
                        settings_3d_margin = float(settings_3d_margin)
                        if settings_3d_margin == math.nan:
                            settings_3d_margin = None

                    settings_3d_width = attributes["settings_3d_width"]
                    if settings_3d_width == "nan":
                        settings_3d_width = None
                    else:
                        settings_3d_width = float(settings_3d_width)
                        if settings_3d_width == math.nan:
                            settings_3d_width = None

                    display_rule = extract_display_rule(attributes)
                    translations = extract_translations(attributes)

                    lt = solution.location_types.get(
                        LocationType.compute_key(admin_id=admin_id)
                    )
                    if lt is None:

                        solution.add_location_type(
                            admin_id=admin_id,
                            display_rule=display_rule,
                            translations=translations,
                            color=color,
                            is_obstacle=is_obstacle,
                            is_selectable=is_selectable,
                            restrictions=restrictions,
                            settings_3d_margin=settings_3d_margin,
                            settings_3d_width=settings_3d_width,
                        )
                    else:
                        # logger.error(f'{lt} with {admin_id} already exists, updating')
                        solution.update_location_type(
                            lt.key,
                            display_rule=display_rule,
                            translations=translations,
                            color=color,
                            is_obstacle=is_obstacle,
                            is_selectable=is_selectable,
                            restrictions=restrictions,
                            settings_3d_margin=settings_3d_margin,
                            settings_3d_width=settings_3d_width,
                        )

            except Exception as e:
                _invalid = f"Invalid location_types: {e}"
                logger.error(_invalid)

                if collect_invalid:
                    issues.append(_invalid)

                raise e
        else:
            logger.debug(f"{solution_level_item.name()} was not a location_type layer")
