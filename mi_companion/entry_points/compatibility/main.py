#!/usr/bin/python
import logging

from jord.qgis_utilities import read_plugin_setting

from integration_system.config import Settings
from mi_companion import PROJECT_NAME, DEFAULT_PLUGIN_SETTINGS

logger = logging.getLogger(__name__)


def run(*, solution_id: str) -> None:
    from integration_system.compatibilization import (
        make_solution_compatible,
    )

    sync_module_settings = Settings()
    sync_module_settings.mapsindoors.username = read_plugin_setting(
        "MAPS_INDOORS_USERNAME",
        default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_USERNAME"],
        project_name=PROJECT_NAME,
    )

    sync_module_settings.mapsindoors.password = read_plugin_setting(
        "MAPS_INDOORS_PASSWORD",
        default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_PASSWORD"],
        project_name=PROJECT_NAME,
    )

    sync_module_settings.mapsindoors.token_endpoint = read_plugin_setting(
        "MAPS_INDOORS_TOKEN_ENDPOINT",
        default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_TOKEN_ENDPOINT"],
        project_name=PROJECT_NAME,
    )
    sync_module_settings.mapsindoors.manager_api_host = read_plugin_setting(
        "MAPS_INDOORS_MANAGER_API_HOST",
        default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_MANAGER_API_HOST"],
        project_name=PROJECT_NAME,
    )
    sync_module_settings.mapsindoors.media_api_host = read_plugin_setting(
        "MAPS_INDOORS_MEDIA_API_HOST",
        default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_MEDIA_API_HOST"],
        project_name=PROJECT_NAME,
    )

    logger.info(f"Running compatiblisation on {solution_id=}")

    make_solution_compatible(solution_id, settings=sync_module_settings)

    logger.info(f"Finished compatiblisation on {solution_id=}")


if __name__ == "__main__":

    def asijdauh():
        kemper_qgis = "717003114802465c9793f5ff"

        logger.basicConfig(level=logging.INFO)

        run(solution_id=kemper_qgis)
