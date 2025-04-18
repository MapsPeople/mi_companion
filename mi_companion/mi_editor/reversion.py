import logging
from typing import Dict, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.mi import SyncLevel, synchronize
from integration_system.model import Solution
from mi_companion import HALF_SIZE
from mi_companion.layer_descriptors import DATABASE_GROUP_DESCRIPTOR

__all__ = ["revert_venues"]

from jord.qgis_utilities import parse_q_value

logger = logging.getLogger(__name__)


def revert_venues(
    original_solution_venues: Dict[str, Dict[str, Solution]],
    mi_hierarchy_group_name: str = DATABASE_GROUP_DESCRIPTOR,
    *,
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
) -> None:
    """

    :param original_solution_venues:
    :param mi_hierarchy_group_name:
    :param progress_bar:
    :return:
    """

    if progress_bar:
        progress_bar.setValue(0)
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    cms_group = layer_tree_root.findGroup(mi_hierarchy_group_name)

    if not cms_group:  # did not find the group
        return

    if progress_bar:
        progress_bar.setValue(10)

    solution_elements = cms_group.children()
    num_solution_elements = len(solution_elements)
    for ith_solution, solution_group_item in enumerate(solution_elements):
        if progress_bar:
            progress_bar.setValue(
                int(10 + (90 * (float(ith_solution + 1) / num_solution_elements)))
            )
        if isinstance(solution_group_item, QgsLayerTreeGroup):
            logger.info(f"Serialising {str(solution_group_item.name())}")

            solution_layer_name = (
                str(solution_group_item.name()).split("(Solution)")[0].strip()
            )

            solution_data_layer_name = "solution_data"

            found_solution_data = False
            solution_data_layer: Optional[Dict] = None
            for c in solution_group_item.children():
                if solution_data_layer_name in c.name():
                    assert (
                        found_solution_data == False
                    ), f"Duplicate {solution_data_layer_name=} for {solution_layer_name=}"
                    found_solution_data = True

                    solution_feature = next(iter(c.layer().getFeatures()))
                    solution_data_layer = {
                        k.name(): parse_q_value(v)
                        for k, v in zip(
                            solution_feature.fields(), solution_feature.attributes()
                        )
                    }

            assert (
                found_solution_data
            ), f"Did not {solution_data_layer_name=} for {solution_layer_name=}"

            solution_external_id = solution_data_layer["external_id"]
            solution_name = solution_data_layer["name"]

            logger.info(f"Converting {str(solution_group_item.name())}")

            venue_elements = solution_group_item.children()
            num_venue_elements = len(venue_elements)
            for ith_venue, venue_group_items in enumerate(venue_elements):
                if progress_bar:
                    progress_bar.setValue(
                        int(
                            10
                            + (
                                90
                                * ((ith_solution + HALF_SIZE) / num_solution_elements)
                                * ((ith_venue + HALF_SIZE) / num_venue_elements)
                            )
                        )
                    )

                venue_key = None
                for building_group_items in venue_group_items.children():
                    if (
                        isinstance(building_group_items, QgsLayerTreeLayer)
                        and "venue" in building_group_items.name()
                        and venue_key is None
                    ):
                        venue_polygon_layer = building_group_items.layer()
                        venue_feature = next(iter(venue_polygon_layer.getFeatures()))

                        venue_attributes = {
                            k.name(): parse_q_value(v)
                            for k, v in zip(
                                venue_feature.fields(), venue_feature.attributes()
                            )
                        }

                        synchronize(
                            original_solution_venues[solution_external_id][
                                venue_attributes["external_id"]
                            ],
                            sync_level=SyncLevel.venue,
                        )
