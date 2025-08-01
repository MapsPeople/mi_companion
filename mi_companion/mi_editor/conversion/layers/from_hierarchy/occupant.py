import logging
from typing import Any, List, Optional

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer

from jord.qgis_utilities import (
    extract_layer_attributes,
)
from sync_module.model import Occupant, Solution

BOOLEAN_LOCATION_TYPE_ATTRS = ()
STR_LOCATION_TYPE_ATTRS = ("key", "translations.en.name")
FLOAT_LOCATION_TYPE_ATTRS = ()
INTEGER_LOCATION_TYPE_ATTRS = ()

logger = logging.getLogger(__name__)

__all__ = ["get_occupant_data"]


def get_occupant_data(
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
            and "occupants".lower().strip()
            in str(solution_level_item.name()).lower().strip()
        ):
            occupants = extract_layer_attributes(solution_level_item)

            try:
                for attributes in occupants:
                    admin_id = attributes["admin_id"]
                    lt = solution.occupants.get(Occupant.compute_key(admin_id=admin_id))
                    if lt is None:
                        solution.add_occupant(
                            location_key=...,  # TODO: FINISH IMPLEMENTATION
                            occupant_template_key=...,
                        )

            except Exception as e:
                _invalid = f"Invalid location_types: {e}"
                logger.error(_invalid)
                if collect_invalid:
                    issues.append(_invalid)
