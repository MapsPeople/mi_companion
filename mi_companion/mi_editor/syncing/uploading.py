import logging

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtGui, QtWidgets, QtWidgets

from .pre_upload_processing import post_process_solution
from .upload import sync_build_venue_solution

logger = logging.getLogger(__name__)


def upload_venue(
    *,
    collect_errors,
    collect_invalid,
    collect_warnings,
    include_media,
    include_occupants,
    issues,
    progress_bar,
    qgis_instance_handle,
    solution,
    solution_depth,
    solution_name,
    upload_venues,
    venue_key,
) -> None:
    post_process_solution(solution)

    if collect_invalid:
        assert upload_venues is False, "Cannot upload venues if collecting invalid"
        title = f"Validation {venue_key}"

        if issues:
            QtWidgets.QMessageBox.critical(None, title, "- " + "\n\n- ".join(issues))
        else:
            QtWidgets.QMessageBox.information(None, title, "No issues found")

        issue_points = []
        for issue in issues:
            if isinstance(issue, str):
                logger.error(issue)
            else:
                logger.error(f"{issue=}")
                issue_points.append(issue)

        if issue_points:
            ...
            # qgis_instance_handle.iface.mapCanvas().setSelection(            issue_points            )
            # add_shapely_layer(qgis_instance_handle=qgis_instance_handle, geoms=issue_points)
            # TODO: Add  shapely layer with issues

    elif upload_venues:
        assert (
            len(issues) == 0
            and not collect_invalid
            and not collect_warnings
            and not collect_errors
        ), (
            f"Did not expect issues: {issues=}, {collect_invalid=}, {collect_warnings=}, {collect_errors=}, "
            f"cannot upload!"
        )
        sync_build_venue_solution(
            qgis_instance_handle=qgis_instance_handle,
            include_media=include_media,
            include_occupants=include_occupants,
            solution=solution,
            solution_depth=solution_depth,
            solution_name=solution_name,
            progress_bar=progress_bar,
        )
