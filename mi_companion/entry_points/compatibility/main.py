#!/usr/bin/python
import logging
from typing import Optional

from jord.qgis_utilities import read_plugin_setting

from integration_system.config import MapsIndoors, Settings, set_settings
from mi_companion import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME

logger = logging.getLogger(__name__)


def run(*, solution_id: str, new_solution_external_id: Optional[str] = None) -> None:
    from integration_system.compatibilization import (
        make_solution_compatible,
    )

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

    logger.info(f"Running compatiblisation on {solution_id=}")

    solution_external_id = None
    if new_solution_external_id:
        solution_external_id = new_solution_external_id

    make_solution_compatible(solution_id, new_external_id=solution_external_id)

    logger.info(f"Finished compatiblisation on {solution_id=}")


if __name__ == "__main__":

    def asijdauh():
        kemper_qgis = "4b2592bdd05342f2ada9cca3"

        run(solution_id=kemper_qgis)

    asijdauh()
