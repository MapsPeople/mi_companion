import logging
from typing import Any, List, Optional

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer

from integration_system.model import LocationType, Solution
from mi_companion.mi_editor.conversion.layers.from_hierarchy.common_attributes import (
    extract_display_rule,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.extraction import (
    extract_layer_attributes,
)

BOOLEAN_LOCATION_TYPE_ATTRS = ()
STR_LOCATION_TYPE_ATTRS = ("name", "admin_id")
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
                for attribute in floor_attributes:
                    admin_id = attribute["admin_id"]
                    lt = solution.location_types.get(
                        LocationType.compute_key(admin_id=admin_id)
                    )
                    if lt is None:
                        name = attribute["name"]

                        display_rule = extract_display_rule(attribute)
                        solution.add_location_type(
                            admin_id=admin_id, name=name, display_rule=display_rule
                        )
                    else:
                        assert (
                            lt.name == attribute["name"]
                        ), f'{lt.name} != {attribute["name"]}'

            except Exception as e:
                _invalid = f"Invalid location_types: {e}"
                logger.error(_invalid)

                if collect_invalid:
                    issues.append(_invalid)
