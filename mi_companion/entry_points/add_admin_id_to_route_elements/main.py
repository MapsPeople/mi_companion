#!/usr/bin/python
import logging

from mi_companion import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME, RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]


def run(*, solution_id: str) -> None:
    """

    :param solution_id:
    :return:
    """

    from sync_module.mi.config import MapsIndoors, Settings, set_settings
    from sync_module.tools.compatibilization import (
        make_route_elements_compatible,
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

    logger.info(f"Running route element compatiblisation on {solution_id=}")

    make_route_elements_compatible(solution_id)

    logger.info(f"Finished route element compatiblisation on {solution_id=}")


if __name__ == "__main__":

    def asijdauh():
        kemper_qgis = "3a8517aefd214ea4948570c8"

        run(solution_id=kemper_qgis)

    asijdauh()
