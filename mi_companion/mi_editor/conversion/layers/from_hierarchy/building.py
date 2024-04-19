import logging
import uuid

import shapely
from jord.shapely_utilities.base import clean_shape

from mi_companion.configuration.constants import (
    HALF_SIZE,
    BUILDING_POLYGON_DESCRIPTOR,
    GENERATE_MISSING_EXTERNAL_IDS,
)
from .floor import add_floor

logger = logging.getLogger(__name__)

__all__ = ["add_building"]


def add_building(
    ith_solution,
    ith_venue,
    num_solution_elements,
    num_venue_elements,
    progress_bar,
    solution,
    venue_group_items,
    venue_key,
):
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    building_elements = venue_group_items.children()
    num_building_elements = len(building_elements)
    for ith_building, building_group_items in enumerate(building_elements):
        if progress_bar:
            progress_bar.setValue(
                int(
                    10
                    + (
                        90
                        * ((ith_solution + HALF_SIZE) / num_solution_elements)
                        * ((ith_venue + HALF_SIZE) / num_venue_elements)
                        * ((ith_building + HALF_SIZE) / num_building_elements)
                    )
                )
            )
        if isinstance(building_group_items, QgsLayerTreeGroup):
            building_key = None
            for floor_group_items in building_group_items.children():
                if (
                    isinstance(floor_group_items, QgsLayerTreeLayer)
                    and BUILDING_POLYGON_DESCRIPTOR.lower()
                    in str(floor_group_items.name()).lower()
                    and venue_key is not None
                    and building_key is None
                ):
                    building_polygon_layer = floor_group_items.layer()
                    building_feature = building_polygon_layer.getFeature(
                        1  # 1 is the first element
                    )

                    building_attributes = {
                        k.name(): v
                        for k, v in zip(
                            building_feature.fields(),
                            building_feature.attributes(),
                        )
                    }

                    if len(building_attributes) == 0:
                        continue
                    else:
                        logger.error(
                            f"Did not find building, skipping {floor_group_items.name()}"
                        )

                    external_id = building_attributes["external_id"]
                    if external_id is None:
                        if GENERATE_MISSING_EXTERNAL_IDS:
                            external_id = uuid.uuid4().hex
                        else:
                            raise ValueError(
                                f"{building_feature} is missing a valid external id"
                            )

                    name = building_attributes["name"]
                    if name is None:
                        name = external_id

                    building_key = solution.add_building(
                        external_id=external_id,
                        name=name,
                        polygon=clean_shape(
                            shapely.from_wkt(building_feature.geometry().asWkt())
                        ),
                        venue_key=venue_key,
                    )
            if building_key:
                floor_elements = building_group_items.children()
                num_floor_elements = len(floor_elements)
                for ith_floor, floor_group_items in enumerate(floor_elements):
                    if progress_bar:
                        progress_bar.setValue(
                            int(
                                10
                                + (
                                    90
                                    * (
                                        (ith_solution + HALF_SIZE)
                                        / num_solution_elements
                                    )
                                    * ((ith_venue + HALF_SIZE) / num_venue_elements)
                                    * (
                                        (ith_building + HALF_SIZE)
                                        / num_building_elements
                                    )
                                    * ((ith_floor + HALF_SIZE) / num_floor_elements)
                                )
                            )
                        )

                    if isinstance(floor_group_items, QgsLayerTreeGroup):
                        add_floor(building_key, floor_group_items, solution)
            else:
                logger.error(f"{building_key=}, skipping")
