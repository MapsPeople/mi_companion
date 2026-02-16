import logging

from mi_plugin import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME, RESOURCE_BASE_PATH
from mi_plugin.mi_editor.authentication.get_credentials_from_auth_manager import (
    get_credentials_from_auth_manager,
)

_logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]

FUNCTION_DESCRIPTION = """Migrate a venue from a solution to another solution (Deletion from original currently not supported, but rather just a copy at the moment)

You can find the venue_admin_id in the venue_polygon layer or in the cms
"""

__doc__ = FUNCTION_DESCRIPTION


def run(
    *,
    from_solution_id: str,
    to_solution_id: str,
    venue_admin_id: str,
    # remove_venue_in_from_solution: bool = False,
) -> None:
    f"""{FUNCTION_DESCRIPTION}



    :param from_solution_id:
    :param to_solution_id:
    :param venue_admin_id:
    :param remove_venue_in_from_solution: DISABLED FOR NOW!
    :return:
    """

    from sync_module.mi.config import MapsIndoors, Settings, set_settings
    from sync_module.tools.migration import migrate_venue
    from jord.qgis_utilities import read_plugin_setting

    mp_username, mp_password = get_credentials_from_auth_manager()

    sync_module_settings = Settings(
        mapsindoors=MapsIndoors(
            username=mp_username,
            password=mp_password,
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
        # remove_venue_in_from_solution=remove_venue_in_from_solution,
    )
