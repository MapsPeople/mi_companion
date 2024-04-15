import logging
from typing import Optional, Dict

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.mi import get_remote_solution, SolutionDepth
from integration_system.mi.config import get_settings, Settings
from integration_system.mi.downloading import get_solution_name_external_id_map
from mi_companion.configuration.constants import (
    MI_HIERARCHY_GROUP_NAME,
    SOLUTION_DESCRIPTOR,
)
from .venue import convert_venues

__all__ = ["layer_hierarchy_to_solution"]


logger = logging.getLogger(__name__)


def convert_solution_layers_to_solution(
    qgis_instance_handle,
    *,
    progress_bar: callable,
    ith_solution: int,
    num_solution_elements,
    solution_group_item,
    settings: Settings,
    solution_depth=SolutionDepth.LOCATIONS,
    include_route_elements=False,
    include_occupants=False,
    include_media=False,
    include_graph=False,
) -> None:
    # TODO: ASSERT SOLUTION_DESCRIPTOR in group name
    assert SOLUTION_DESCRIPTOR in str(solution_group_item.name())

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

                solution_feature = c.layer().getFeature(1)  # 1 is first element
                solution_data_layer = {
                    k.name(): v
                    for k, v in zip(
                        solution_feature.fields(), solution_feature.attributes()
                    )
                }

        assert (
            found_solution_data
        ), f"Did not find {solution_data_layer_name=} for {solution_layer_name=}"

        solution_external_id = solution_data_layer["external_id"]
        solution_customer_id = solution_data_layer["customer_id"]
        solution_occupants_enabled = solution_data_layer["occupants_enabled"]
        solution_name = solution_data_layer["name"]

        if solution_external_id is None:
            solution_external_id = solution_name

        if (
            solution_external_id
            in get_solution_name_external_id_map(settings=settings).values()
        ):
            existing_solution = get_remote_solution(
                solution_external_id,
                venue_keys=[],
                settings=settings,
                depth=solution_depth,
                include_route_elements=include_route_elements,
                include_occupants=include_occupants,
                include_media=include_media,
                include_graph=include_graph,
            )
        else:
            existing_solution = None

        logger.info(f"Converting {str(solution_group_item.name())}")

        convert_venues(
            qgis_instance_handle,
            solution_group_item=solution_group_item,
            existing_solution=existing_solution,
            progress_bar=progress_bar,
            solution_external_id=solution_external_id,
            solution_name=solution_name,
            solution_customer_id=solution_customer_id,
            solution_occupants_enabled=solution_occupants_enabled,
            settings=settings,
            ith_solution=ith_solution,
            num_solution_elements=num_solution_elements,
            solution_depth=solution_depth,
            include_route_elements=include_route_elements,
            include_occupants=include_occupants,
            include_media=include_media,
            include_graph=include_graph,
        )


def layer_hierarchy_to_solution(
    qgis_instance_handle,
    mi_hierarchy_group_name: str = MI_HIERARCHY_GROUP_NAME,
    *,
    settings: Optional[Settings] = None,
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
    solution_depth=SolutionDepth.LOCATIONS,
    include_route_elements=False,
    include_occupants=False,
    include_media=False,
    include_graph=False,
) -> None:
    if settings is None:
        settings = get_settings()

    if False:
        ...
        # from PyQt6.QtGui import QAction
        # @pyqtSlot(int)
        # def addedGeometry(self, intValue):
        # fun stuff here

        def show_attribute_table(layer) -> None:
            if layer is None:
                layer = qgis_instance_handle.iface.activeLayer()
            att_dialog = qgis_instance_handle.iface.showAttributeTable(layer)
            # att_dialog.findChild(QAction, "mActionSelectedFilter").trigger()

        # signals.reconnect_signal(vlayer.featureAdded, show_attribute_table)
        # for feat in iface.activeLayer().getFeatures():
        #    iface.activeLayer().setSelectedFeatures([feat.id()])

    if progress_bar:
        progress_bar.setValue(0)

    layer_tree_root = QgsProject.instance().layerTreeRoot()

    mi_group = layer_tree_root.findGroup(mi_hierarchy_group_name)

    if not mi_group:  # did not find the group
        return

    if progress_bar:
        progress_bar.setValue(10)

    solution_elements = mi_group.children()
    num_solution_elements = len(solution_elements)
    for ith_solution, solution_group_item in enumerate(solution_elements):
        convert_solution_layers_to_solution(
            qgis_instance_handle,
            progress_bar=progress_bar,
            ith_solution=ith_solution,
            num_solution_elements=num_solution_elements,
            solution_group_item=solution_group_item,
            settings=settings,
            solution_depth=solution_depth,
            include_route_elements=include_route_elements,
            include_occupants=include_occupants,
            include_media=include_media,
            include_graph=include_graph,
        )
