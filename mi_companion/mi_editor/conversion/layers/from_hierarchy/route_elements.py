import logging
from typing import Any

import shapely

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

from integration_system.model import DoorType, Solution
from mi_companion.configuration.constants import VERBOSE
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db

logger = logging.getLogger(__name__)

__all__ = ["add_doors"]


def add_doors(
    *, floor_index: int, graph_key: str, location_group_items: Any, solution: Solution
) -> None:
    doors_linestring_layer = location_group_items.layer()
    for door_feature in doors_linestring_layer.getFeatures():
        door_attributes = {
            k.name(): v
            for k, v in zip(
                door_feature.fields(),
                door_feature.attributes(),
            )
        }

        door_type = door_attributes["door_type"]
        if isinstance(door_type, str):
            ...
        elif isinstance(door_type, QVariant):
            # logger.warning(f"{typeToDisplayString(type(v))}")
            if door_type.isNull():  # isNull(v):
                door_type = None
            else:
                door_type = door_type.value()

        door_key = solution.add_door(
            door_attributes["external_id"],
            linestring=prepare_geom_for_mi_db(
                shapely.from_wkt(door_feature.geometry().asWkt())
            ),
            door_type=DoorType.__getitem__(door_type),
            floor_index=floor_index,
            graph_key=graph_key,
        )
        if VERBOSE:
            logger.info("added door", door_key)
