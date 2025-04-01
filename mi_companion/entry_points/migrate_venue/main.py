#!/usr/bin/python
import logging

from integration_system.config import MapsIndoors, Settings, set_settings
from integration_system.migration import migrate_venue
from jord.qgis_utilities import read_plugin_setting
from mi_companion import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME

logger = logging.getLogger(__name__)
__all__ = []


def run(
    *,
    from_solution_id: str,
    to_solution_id: str,
    venue_admin_id: str,
    remove_venue_in_from_solution: bool = False,
) -> None:
    """

    You can find the venue_admin_id in the venue_polygon layer or in the cms

    :param from_solution_id:
    :param to_solution_id:
    :param venue_admin_id:
    :param remove_venue_in_from_solution: DISABLED FOR NOW!
    :return:
    """

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

    migrate_venue(
        from_solution_id=from_solution_id,
        to_solution_id=to_solution_id,
        venue_admin_id=venue_admin_id,
        remove_venue_in_from_solution=remove_venue_in_from_solution,
    )
