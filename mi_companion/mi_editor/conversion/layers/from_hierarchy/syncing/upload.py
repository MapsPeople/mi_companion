import logging
from itertools import count
from typing import Any, Collection, List, Optional

import shapely

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

from integration_system.mi import (
    MIOperation,
    SolutionDepth,
    SyncLevel,
    default_matcher,
    default_strategy,
    strategy_solver,
    synchronize,
)
from integration_system.model import (
    DIFFERENCE_GROUP_NAME,
    Graph,
    SHAPELY_DIFFERENCE_DESCRIPTION,
    Solution,
)
from mi_companion import VERBOSE
from mi_companion.configuration.options import read_bool_setting
from mi_companion.gui.message_box import ResizableMessageBox
from mi_companion.mi_editor.conversion.projection import (
    MI_EPSG_NUMBER,
)

logger = logging.getLogger(__name__)

USE_EXISTING_GRAPH = True


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

    venue_name = next(iter(solution.venues)).name
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
        msg_box.setText(f"The {solution_name}:{venue_name} venue has been modified.")
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

    sync_level = SyncLevel.VENUE
    strategy = dict(default_strategy())
    if USE_EXISTING_GRAPH:
        strategy[Graph] = default_matcher, None  # Do not update graph
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
        include_route_elements=read_bool_setting(
            "ADD_ROUTE_ELEMENTS"
        ),  # include_route_elements,
        include_occupants=include_occupants,
        include_media=include_media,
        include_graph=read_bool_setting("ADD_GRAPH"),  # include_graph,
        operation_solver=strategy_solver(
            sync_level=sync_level, depth=solution_depth, strategy=strategy
        ),
    )

    if VERBOSE:
        logger.info("Synchronised")

    if success:
        QtWidgets.QMessageBox.information(
            None,
            window_title,
            f"Successfully uploaded {solution_name}:{venue_name} venue",
        )


def show_differences(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    solution_name: str,
    operations: Collection[MIOperation],
) -> None:
    mi_db_difference_group = (
        QgsProject.instance().layerTreeRoot().findGroup(DIFFERENCE_GROUP_NAME)
    )

    if not mi_db_difference_group:  # did not find the group
        mi_db_difference_group = (
            QgsProject.instance().layerTreeRoot().insertGroup(0, DIFFERENCE_GROUP_NAME)
        )

    solution_difference_group = mi_db_difference_group.findGroup(solution_name)

    if not solution_difference_group:  # did not find the group
        solution_difference_group = mi_db_difference_group.insertGroup(0, solution_name)

    venue = next(iter(solution.venues))
    venue_diff_name = venue.name

    venue_difference_group = solution_difference_group.findGroup(venue_diff_name)

    if venue_difference_group:  # Found the group
        for node in [
            child
            for child in venue_difference_group.children()
            # if child.nodeType() == 0
        ]:
            venue_difference_group.removeChildNode(node)
    else:  # did not find the group
        venue_difference_group = solution_difference_group.insertGroup(
            0, venue_diff_name
        )

    for o in operations:
        differences = {}
        operation_counter = iter(count())
        from jord.shapely_utilities import is_multi

        if SHAPELY_DIFFERENCE_DESCRIPTION in o.context:
            for i in o.context.split(SHAPELY_DIFFERENCE_DESCRIPTION)[1:]:
                diff_op_ith = next(
                    operation_counter
                )  # TODO: ALL OF THIS CAN BE IMPROVED! WITH SOME proper IDs

                differences[diff_op_ith] = shapely.wkt.loads(
                    i.replace("\n", "")[0].replace("\n", "").strip()
                )  # Also one parses a single geom per operation
                if is_multi(differences[diff_op_ith]):
                    rep_points = []
                    for g in differences[diff_op_ith].geoms:
                        rep_points.append(g.representative_point())
                    differences[f"{diff_op_ith}_coherence"] = shapely.LineString(
                        rep_points
                    )

        try:
            import geopandas

            df = geopandas.GeoDataFrame(
                {"op_ith": differences.keys(), "geometry": differences.values()},
                crs=f"EPSG:{MI_EPSG_NUMBER}",
                geometry="geometry",
            )
            from jord.qlive_utilities import add_dataframe_layer

            add_dataframe_layer(
                qgis_instance_handle=qgis_instance_handle,
                dataframe=df,
                geometry_column="geometry",
                name=f"{o.item_type.__name__} differences",
                group=venue_difference_group,
                crs=f"EPSG:{MI_EPSG_NUMBER}",
            )
        except Exception as e:  # TODO: HANDLE MIxed GEOM TYPES!
            logger.error(e)
