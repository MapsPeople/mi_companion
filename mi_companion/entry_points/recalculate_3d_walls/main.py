#!/usr/bin/python
import logging
from typing import Optional

from mi_companion import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME, RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]


def run(*, solution_id: str, venue_ids: Optional[str] = None) -> None:
    """

    :param venue_ids: comma seperated
    :param solution_id:
    :return:
    """

    from sync_module.mi.config import MapsIndoors, Settings, set_settings
    from sync_module.mi import call_manager_api
    from jord.qgis_utilities import read_plugin_setting

    sync_module_settings = Settings(
        mapsindoors=MapsIndoors(
            username=read_plugin_setting(
                "MAPS_INDOORS_USERNAME",
                default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_USERNAME"],
                project_name=PROJECT_NAME,
            ),
            password=read_plugin_setting(
                "MAPS_INDOORS_PASSWORD",
                default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_PASSWORD"],
                project_name=PROJECT_NAME,
            ),
            token_endpoint=read_plugin_setting(
                "MAPS_INDOORS_TOKEN_ENDPOINT",
                default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_TOKEN_ENDPOINT"],
                project_name=PROJECT_NAME,
            ),
            manager_api_host=read_plugin_setting(
                "MAPS_INDOORS_MANAGER_API_HOST",
                default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_MANAGER_API_HOST"],
                project_name=PROJECT_NAME,
            ),
            media_api_host=read_plugin_setting(
                "MAPS_INDOORS_MEDIA_API_HOST",
                default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_MEDIA_API_HOST"],
                project_name=PROJECT_NAME,
            ),
        )
    )

    set_settings(sync_module_settings)

    solution_id = solution_id.strip()

    if venue_ids:
        venue_ids = venue_ids.split(",")
        for venue_id in venue_ids:
            venue_id = venue_id.strip()
            call_manager_api(
                "PUT",
                f"/{solution_id}/api/derivedgeometry",
                query_params={"venueId": venue_id},
            )
    else:
        call_manager_api("PUT", f"/{solution_id}/api/derivedgeometry")

    # noinspection PyUnresolvedReferences
    from qgis.PyQt.QtWidgets import (
        QMessageBox,
    )

    # noinspection PyUnresolvedReferences
    from qgis.PyQt import QtGui, QtWidgets, uic

    QtWidgets.QMessageBox.information(
        None,
        "Derived Geometry",
        f"Derived is now being recomputed for solution {solution_id}",
    )


if __name__ == "__main__":

    def asijdauh():
        kemper_qgis = "4b2592bdd05342f2ada9cca3"

        run(solution_id=kemper_qgis)

    asijdauh()
