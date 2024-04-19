import logging
import uuid

import shapely
from jord.shapely_utilities.base import clean_shape

from mi_companion.configuration.constants import (
    FLOOR_POLYGON_DESCRIPTOR,
    GENERATE_MISSING_EXTERNAL_IDS,
)
from .location import add_floor_contents

logger = logging.getLogger(__name__)


__all__ = ["add_floor"]


def add_floor(building_key, floor_group_items, solution):
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    floor_key = None
    for inventory_group_items in floor_group_items.children():
        if (
            isinstance(
                inventory_group_items,
                QgsLayerTreeLayer,
            )
            and FLOOR_POLYGON_DESCRIPTOR.lower()
            in str(inventory_group_items.name()).lower()
            and building_key is not None
            and floor_key is None
        ):
            floor_polygon_layer = inventory_group_items.layer()
            floor_feature = floor_polygon_layer.getFeature(1)  # 1 is first element

            floor_attributes = {
                k.name(): v
                for k, v in zip(
                    floor_feature.fields(),
                    floor_feature.attributes(),
                )
            }
            external_id = floor_attributes["external_id"]
            if external_id is None:
                if GENERATE_MISSING_EXTERNAL_IDS:
                    external_id = uuid.uuid4().hex
                else:
                    raise ValueError(f"{floor_feature} is missing a valid external id")

            name = floor_attributes["name"]
            if name is None:
                name = external_id

            floor_key = solution.add_floor(
                external_id=external_id,
                name=name,
                floor_index=floor_attributes["floor_index"],
                polygon=clean_shape(shapely.from_wkt(floor_feature.geometry().asWkt())),
                building_key=building_key,
            )
    assert floor_key, floor_key
    add_floor_contents(
        floor_group_items=floor_group_items,
        floor_key=floor_key,
        solution=solution,
        graph_key=(
            solution.floors.get(floor_key).building.venue.graph.key
            if solution.floors.get(floor_key).building.venue.graph
            else None
        ),
        floor_index=floor_attributes["floor_index"],
    )
