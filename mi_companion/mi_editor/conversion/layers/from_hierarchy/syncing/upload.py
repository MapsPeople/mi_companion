import logging
from typing import Any, Collection, List, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

from sync_module.mi import (
    MIOperation,
    SolutionDepth,
    SyncLevel,
    default_matcher,
    default_strategy,
    strategy_solver,
    synchronize,
)
from sync_module.model import (
    Graph,
    Solution,
)
from mi_companion import VERBOSE
from mi_companion.configuration import read_bool_setting
from mi_companion.gui.message_box import ResizableMessageBox
from .operation_visualisation import show_differences
from ..constants import DISABLE_GRAPH_EDIT

logger = logging.getLogger(__name__)

__all__ = ["sync_build_venue_solution"]


def sync_build_venue_solution(
    *,
    qgis_instance_handle: Any,
    include_graph: bool,  # IGNORED FOR NOW
    include_media: bool,
    include_occupants: bool,
    include_route_elements: bool,  # IGNORED
    solution: Solution,
    solution_depth: SolutionDepth,
    solution_name: str,
    progress_bar: Optional[Any] = None,
) -> None:
    """if False:
    existing_venue_solution = get_remote_solution(
        solution_name,
        venue_keys=[venue_key],
        include_graph=False,
    )
    if existing_venue_solution:
        for occupant in existing_solution.occupants:
            solution.add_occupant(
                location_key=occupant.location.key,
                occupant_template_key=(
                    occupant.template.key if occupant.template else None
                ),
                is_anchor=occupant.is_anchor,
                is_operating=occupant.is_operating,
                aliases=occupant.aliases,
                business_hours=occupant.business_hours,
                address=occupant.address,
                contact=occupant.contact,
                media_key=(occupant.logo.key if occupant.logo else None),
            )

    :param qgis_instance_handle:
    :param include_graph:
    :param include_media:
    :param include_occupants:
    :param include_route_elements:
    :param solution:
    :param solution_depth:
    :param solution_name:
    :param progress_bar:
    :return:
    """

    if VERBOSE:
        logger.info("Synchronising")

    venue_name = (
        next(iter(solution.venues)).translations[solution.default_language].name
    )
    window_title = f"Sync {solution_name}:{venue_name} venue"

    def solving_progress_bar_callable(ith: int, total: int) -> None:
        progress_bar.setValue(int(20 + (ith / total) * 80))
        logger.debug(f"Solving: {ith}/{total}")

    def operation_progress_bar_callable(
        operation: MIOperation, ith: int, total: int
    ) -> None:
        progress_bar.setValue(int(20 + (ith / total) * 80))
        logger.debug(operation)
        logger.debug(f"Synchronising: {ith}/{total}")

        # qgis_instance_handle.iface.messageBar().popWidget()
        # qgis_instance_handle.iface.messageBar().pushMessage(before, text, level=level, duration=duration)

    def confirmation_dialog(operations: List[MIOperation]) -> bool:
        if operations is None or len(operations) == 0:
            QtWidgets.QMessageBox.information(
                None, window_title, "No difference was found, no operations"
            )
            return False

        def aggregate_operation_description(
            operation: Collection[MIOperation],
        ) -> str:
            desc = ""
            for o in operation:
                desc += f"{o.operation_type.name}: {len(o.item_keys)} {o.item_type.__name__}(s)\n"

            return desc

        msg_box = ResizableMessageBox(
            # parent=qgis_instance_handle.iface
        )
        msg_box.setWindowFlags(
            QtCore.Qt.Dialog  # & ~QtCore.Qt.MSWindowsFixedSizeDialogHint
        )
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle(window_title)
        text_msg = f"The {solution_name}:{venue_name} venue has been modified."

        if read_bool_setting("UPLOAD_OSM_GRAPH"):
            text_msg += "\nNote: Graph will always update ATM"

        msg_box.setText(text_msg)
        msg_box.setInformativeText(
            f"Do you want to sync following changes?\n\n{aggregate_operation_description(operations)}"
        )
        msg_box.setDetailedText("\n\n".join([str(o) for o in operations]))
        msg_box.setStandardButtons(
            QtWidgets.QMessageBox.Yes
            | QtWidgets.QMessageBox.No
            | QtWidgets.QMessageBox.Help
        )
        msg_box.setDefaultButton(QtWidgets.QMessageBox.No)
        msg_box.setEscapeButton(QtWidgets.QMessageBox.No)
        reply = msg_box.exec()

        if reply == QtWidgets.QMessageBox.Yes:
            return True

        if reply == QtWidgets.QMessageBox.Help:
            show_differences(
                qgis_instance_handle=qgis_instance_handle,
                solution=solution,
                solution_name=solution_name,
                operations=operations,
            )

        return False

    sync_level = SyncLevel.venue

    strategy = dict(default_strategy())
    if (
        not (
            read_bool_setting("UPDATE_GRAPH") and read_bool_setting("UPLOAD_OSM_GRAPH")
        )
        or DISABLE_GRAPH_EDIT
    ):
        strategy[Graph] = default_matcher, None  # Do not update graph

    try:
        success = synchronize(
            solution,
            sync_level=sync_level,
            operation_progress_callback=(
                operation_progress_bar_callable
                if read_bool_setting("OPERATION_PROGRESS_BAR_ENABLED")
                else None
            ),
            solving_progress_callback=(
                solving_progress_bar_callable
                if read_bool_setting("SOLVING_PROGRESS_BAR_ENABLED")
                else None
            ),
            confirmation_callback=(
                confirmation_dialog
                if read_bool_setting("CONFIRMATION_DIALOG_ENABLED")
                else None
            ),
            depth=solution_depth,
            include_route_elements=read_bool_setting("ADD_ROUTE_ELEMENTS")
            and include_route_elements,
            include_occupants=include_occupants,
            include_media=include_media,
            include_graph=read_bool_setting("ADD_GRAPH") and include_graph,
            operation_solver=strategy_solver(
                sync_level=sync_level, depth=solution_depth, strategy=strategy
            ),
        )
    except Exception as e:
        QtWidgets.QMessageBox.critical(
            None,
            window_title,
            f"ERROR: {solution_name}:{venue_name} venue could not be uploaded, {e}",
        )
        logger.error(
            f'Error synchronising, try running the "Compatibility" button to fix solution {e}'
        )
        raise e

    if VERBOSE:
        logger.info("Synchronised")

    if success:
        QtWidgets.QMessageBox.information(
            None,
            window_title,
            f"Successfully uploaded {solution_name}:{venue_name} venue",
        )
