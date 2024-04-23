import logging
from itertools import count
from typing import List, Collection

import shapely
from jord.qgis_utilities import read_plugin_setting

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

from integration_system.constants import (
    DIFFERENCE_GROUP_NAME,
    SHAPELY_DIFFERENCE_DESCRIPTION,
)
from integration_system.mi import MIOperation, synchronize, SyncLevel
from mi_companion import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME
from mi_companion.configuration.constants import VERBOSE
from mi_companion.gui.message_box import ResizableMessageBox
from mi_companion.mi_editor.conversion.projection import (
    should_reproject,
    GDS_EPSG_NUMBER,
    MI_EPSG_NUMBER,
)
from .pre_upload_processing import post_process_solution

logger = logging.getLogger(__name__)


def sync_build_venue_solution(
    qgis_instance_handle,
    include_graph,  # IGNORED FOR NOW
    include_media,
    include_occupants,
    include_route_elements,  # IGNORED
    settings,
    solution,
    solution_depth,
    solution_name,
    progress_bar,
):
    """if False:
    existing_venue_solution = get_remote_solution(
        solution_name,
        venue_keys=[venue_key],
        settings=settings,
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
            )"""
    if VERBOSE:
        logger.info("Synchronising")

    post_process_solution(solution)

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
        window_title = f"Sync {solution_name} Venues"

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
                desc += f"{o.operation_type.name}: {len(o.object_keys)} {o.object_type.__name__}(s)\n"

            return desc

        msg_box = ResizableMessageBox(
            # parent=qgis_instance_handle.iface
        )
        msg_box.setWindowFlags(
            QtCore.Qt.Dialog  # & ~QtCore.Qt.MSWindowsFixedSizeDialogHint
        )
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle(window_title)
        msg_box.setText(f"The {solution_name} venue(s) has been modified.")
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

    synchronize(
        solution,
        sync_level=SyncLevel.VENUE,
        settings=settings,
        operation_progress_callback=(
            operation_progress_bar_callable
            if read_plugin_setting(
                "OPERATION_PROGRESS_BAR_ENABLED",
                default_value=DEFAULT_PLUGIN_SETTINGS["OPERATION_PROGRESS_BAR_ENABLED"],
                project_name=PROJECT_NAME,
            )
            else None
        ),
        solving_progress_callback=(
            solving_progress_bar_callable
            if read_plugin_setting(
                "SOLVING_PROGRESS_BAR_ENABLED",
                default_value=DEFAULT_PLUGIN_SETTINGS["SOLVING_PROGRESS_BAR_ENABLED"],
                project_name=PROJECT_NAME,
            )
            else None
        ),
        confirmation_callback=(
            confirmation_dialog
            if read_plugin_setting(
                "CONFIRMATION_DIALOG_ENABLED",
                default_value=DEFAULT_PLUGIN_SETTINGS["CONFIRMATION_DIALOG_ENABLED"],
                project_name=PROJECT_NAME,
            )
            else None
        ),
        depth=solution_depth,
        include_route_elements=read_plugin_setting(
            "SYNC_GRAPH_AND_ROUTE_ELEMENTS",
            default_value=DEFAULT_PLUGIN_SETTINGS["SYNC_GRAPH_AND_ROUTE_ELEMENTS"],
            project_name=PROJECT_NAME,
        ),  # include_route_elements,
        include_occupants=include_occupants,
        include_media=include_media,
        include_graph=read_plugin_setting(
            "SYNC_GRAPH_AND_ROUTE_ELEMENTS",
            default_value=DEFAULT_PLUGIN_SETTINGS["SYNC_GRAPH_AND_ROUTE_ELEMENTS"],
            project_name=PROJECT_NAME,
        ),  # include_graph,
    )

    if VERBOSE:
        logger.info("Synchronised")


def show_differences(
    *, qgis_instance_handle, solution, solution_name, operations
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

                differences[diff_op_ith] = shapely.from_wkt(
                    i.split("\n")[0].strip("\n").strip()
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
                name=f"{o.object_type.__name__} differences",
                group=venue_difference_group,
                crs=f"EPSG:{MI_EPSG_NUMBER}",
            )
        except Exception as e:  # TODO: HANDLE MIxed GEOM TYPES!
            logger.error(e)
