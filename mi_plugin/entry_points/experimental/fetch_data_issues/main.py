import logging

from jord.qgis_utilities import read_plugin_setting
from mi_plugin import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME, RESOURCE_BASE_PATH
from mi_plugin.mi_editor.authentication.get_credentials_from_auth_manager import (
    get_credentials_from_auth_manager,
)
from sync_module.mi import call_manager_api
from sync_module.mi.config import MapsIndoors, Settings, set_settings

_logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]
FUNCTION_DESCRIPTION = """Fetch data issue from an endpoint in the ManagerAPI
"""
__doc__ = FUNCTION_DESCRIPTION


def run(*, solution_id: str) -> None:
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

    solution_id = solution_id.strip()

    data_issues = call_manager_api("GET", f"/api/dataissues/details/{solution_id}")

    from qgis.PyQt import QtWidgets

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
