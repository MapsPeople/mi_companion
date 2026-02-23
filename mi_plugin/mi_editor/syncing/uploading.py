import logging
from typing import Any, List, Optional, Union

from qgis.PyQt import QtWidgets

from sync_module.mi import SolutionDepth
from sync_module.model import Solution
from .pre_upload_processing import post_process_solution
from .upload import sync_build_venue_solution

_logger = logging.getLogger(__name__)


def upload_venue(
    *,
    collect_errors: bool,
    collect_invalid: bool,
    collect_warnings: bool,
    include_media: bool,
    include_occupants: bool,
    issues: List[Union[str, Any]],
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
    qgis_instance_handle: Any,
    solution: Solution,
    solution_depth: SolutionDepth,
    solution_name: str,
    upload_venues: bool,
    venue_key: str,
) -> None:
    """

    :param collect_errors:
    :type collect_errors:
    :param collect_invalid:
    :type collect_invalid:
    :param collect_warnings:
    :type collect_warnings:
    :param include_media:
    :type include_media:
    :param include_occupants:
    :type include_occupants:
    :param issues:
    :type issues:
    :param progress_bar:
    :type progress_bar:
    :param qgis_instance_handle:
    :type qgis_instance_handle:
    :param solution:
    :type solution:
    :param solution_depth:
    :type solution_depth:
    :param solution_name:
    :type solution_name:
    :param upload_venues:
    :type upload_venues:
    :param venue_key:
    :type venue_key:
    """
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
                _logger.error(issue)
            else:
                _logger.error(f"{issue=}")
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
