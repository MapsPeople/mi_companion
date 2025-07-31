#!/usr/bin/python
import logging
from typing import Optional

from mi_companion import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME, RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]


def run(*, solution_id: str, new_solution_external_id: Optional[str] = None) -> None:
    """

    :param solution_id:
    :param new_solution_external_id:
    :return:
    """
    from sync_module.mi.config import MapsIndoors, Settings, set_settings
    from sync_module.tools.solution import (
        get_or_set_solution_external_id,
    )
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

    get_or_set_solution_external_id(
        solution_id, new_external_id=new_solution_external_id
    )

    # noinspection PyUnresolvedReferences
    from qgis.PyQt.QtWidgets import (
        QMessageBox,
    )

    # noinspection PyUnresolvedReferences
    from qgis.PyQt import QtGui, QtWidgets, uic

    QtWidgets.QMessageBox.information(
        None,
        "Assigned external ID",
        f"Solution {solution_id} now has an external ID of {new_solution_external_id}",
    )


if __name__ == "__main__":

    def asijdauh():
        kemper_qgis = "4b2592bdd05342f2ada9cca3"

        run(solution_id=kemper_qgis)

    asijdauh()
