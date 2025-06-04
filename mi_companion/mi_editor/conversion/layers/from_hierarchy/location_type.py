import logging
from typing import Any, List, Optional

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer

from integration_system.model import LocationType, Solution
from jord.qgis_utilities import (
    extract_layer_attributes,
)
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
                        )
                    else:
                        # logger.error(f'{lt} with {admin_id} already exists, updating')
                        solution.update_location_type(
                            lt.key, display_rule=display_rule, translations=translations
                        )

            except Exception as e:
                _invalid = f"Invalid location_types: {e}"
                logger.error(_invalid)

                if collect_invalid:
                    issues.append(_invalid)
        else:
            logger.error(f"{solution_level_item.name()} was not a location_type layer")
