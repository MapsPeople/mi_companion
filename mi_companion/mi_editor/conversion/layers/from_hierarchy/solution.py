import logging
from typing import Any, Callable, Dict, List, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from jord.qgis_utilities import parse_q_value
from mi_companion import UPLOAD_ERROR_CONFIRMATION_TITLE
from mi_companion.layer_descriptors import (
    DATABASE_GROUP_DESCRIPTOR,
    SOLUTION_DATA_DESCRIPTOR,
    SOLUTION_GROUP_DESCRIPTOR,
)
from sync_module.mi import (
    SolutionDepth,
    get_remote_solution,
    get_solution_name_external_id_map,
)
from sync_module.model import ImplementationStatus, Solution
from .venue import convert_solution_venues

__all__ = ["layer_hierarchy_to_solution", "convert_solution_layers_to_solution"]

logger = logging.getLogger(__name__)


def convert_solution_layers_to_solution(
    qgis_instance_handle: Any,
    *,
    progress_bar: Callable,
    mi_group: Any,
    solution_depth: SolutionDepth = SolutionDepth.obstacles,
    include_occupants: bool = False,
    include_media: bool = False,
    upload_venues: bool = True,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    collect_invalid: bool = False,
) -> Optional[List[Solution]]:
    mi_group_children = mi_group.children()
    num_mi_group_elements = len(mi_group_children)

    if num_mi_group_elements == 0:
        logger.warning("No solutions to upload")
        return

    if upload_venues:
        assert not (collect_invalid or collect_warnings or collect_errors), (
            f"collect_invalid={collect_invalid}, "
            f"collect_warnings={collect_warnings}, "
            f"collect_errors={collect_errors} are not "
            f"supported when upload_venues="
            f"{upload_venues}"
        )

    solutions = []
    issues = []

    for ith_child, mi_group_child in enumerate(mi_group_children):
        if SOLUTION_GROUP_DESCRIPTOR not in str(mi_group_child.name()):
            _warning = f"{mi_group_child=} was skipped, did not contain {SOLUTION_GROUP_DESCRIPTOR}"
            logger.warning(_warning)
            if collect_warnings:
                issues.append(_warning)
            return

        if progress_bar:
            progress_bar.setValue(
                int(10 + (90 * (float(ith_child + 1) / num_mi_group_elements)))
            )
        if not isinstance(mi_group_child, QgsLayerTreeGroup):
            _warning = f"{mi_group_child=} was skipped"

            logger.warning(_warning)
            if collect_warnings:
                issues.append(_warning)
            continue

        logger.info(f"Serialising {str(mi_group_child.name())}")

        solution_layer_name = str(mi_group_child.name()).split("(Solution)")[0].strip()

        found_solution_data = False
        solution_data: Optional[Dict] = None

        if len(mi_group_child.children()) == 0:
            _warning = "No venues to upload"
            logger.warning(_warning)
            if collect_warnings:
                issues.append(_warning)

            continue

        for child_solution_group in mi_group_child.children():
            if SOLUTION_DATA_DESCRIPTOR in child_solution_group.name():
                assert (
                    found_solution_data == False
                ), f"Duplicate {SOLUTION_DATA_DESCRIPTOR=} for {solution_layer_name=}"

                found_solution_data = True

                solution_point_feature_layer = next(
                    iter(child_solution_group.layer().getFeatures())
                )
                solution_data = {
                    k.name(): parse_q_value(v)
                    for k, v in zip(
                        solution_point_feature_layer.fields(),
                        solution_point_feature_layer.attributes(),
                    )
                }

        if not solution_data:
            _error = f"Did not find solution_data layer, skipping {solution_layer_name}"

            logger.error(_error)

            reply = QMessageBox.question(
                None,
                UPLOAD_ERROR_CONFIRMATION_TITLE,
                _error,
                QMessageBox.Ok,
                QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                raise Exception(_error)

            if collect_errors:
                issues.append(_error)
            continue

        solution_external_id = solution_data["external_id"]
        solution_customer_id = solution_data["customer_id"]
        solution_occupants_enabled = solution_data["occupants_enabled"]
        solution_name = solution_data["name"]
        solution_available_languages = solution_data["available_languages"]

        solution_implementation_type = ImplementationStatus(
            solution_data["implementation_type"]
        )
        solution_default_language = solution_data["default_language"]

        # cached_solution_object =solution_data['cached_solution_object'] # TODO: Store a string to cached
        #  Solution object pickle

        if solution_external_id is None:
            solution_external_id = solution_name

        if solution_external_id in get_solution_name_external_id_map().values():
            existing_solution = get_remote_solution(
                solution_external_id,
                venue_keys=[],  # No Venues
                depth=solution_depth,
                include_occupants=include_occupants,
                include_media=include_media,
            )
        else:
            existing_solution = None

        logger.info(f"Converting {str(mi_group_child.name())}")

        solutions.extend(
            convert_solution_venues(
                qgis_instance_handle,
                mi_group_child=mi_group_child,
                existing_solution=existing_solution,
                progress_bar=progress_bar,
                solution_external_id=solution_external_id,
                solution_name=solution_name,
                solution_customer_id=solution_customer_id,
                solution_occupants_enabled=solution_occupants_enabled,
                solution_available_languages=solution_available_languages,
                solution_implementation_type=solution_implementation_type,
                solution_default_language=solution_default_language,
                ith_solution=ith_child,
                num_solution_elements=num_mi_group_elements,
                solution_depth=solution_depth,
                include_occupants=include_occupants,
                include_media=include_media,
                upload_venues=upload_venues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
                issues=issues,
            )
        )

    return solutions


def layer_hierarchy_to_solution(
    qgis_instance_handle: Any,
    mi_hierarchy_group_name: str = DATABASE_GROUP_DESCRIPTOR,
    *,
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
    solution_depth: SolutionDepth = SolutionDepth.obstacles,
    include_occupants: bool = False,
    include_media: bool = False,
) -> None:
    """

    :param qgis_instance_handle:
    :param mi_hierarchy_group_name:
    :param progress_bar:
    :param solution_depth:
    :param include_route_elements:
    :param include_occupants:
    :param include_media:
    :param include_graph:
    :return:
    """
    if False:
        ...

        # from PyQt6.QtGui import QAction
        # @pyqtSlot(int)
        # def addedGeometry(self, intValue):
        # fun stuff here

        def show_attribute_table(layer) -> None:
            if layer is None:
                layer = qgis_instance_handle.iface_.activeLayer()
            att_dialog = qgis_instance_handle.iface_.showAttributeTable(layer)
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

    convert_solution_layers_to_solution(
        qgis_instance_handle,
        progress_bar=progress_bar,
        mi_group=mi_group,
        solution_depth=solution_depth,
        include_occupants=include_occupants,
        include_media=include_media,
    )
