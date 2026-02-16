import logging
from textwrap import indent
from typing import Optional

from mi_plugin import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME, RESOURCE_BASE_PATH
from mi_plugin.mi_editor.authentication.get_credentials_from_auth_manager import (
    get_credentials_from_auth_manager,
)

_logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]
FUNCTION_DESCRIPTION = """Add an MI layer to the project from available options
"""

__doc__ = FUNCTION_DESCRIPTION


def run(*, solution_id: str, new_solution_external_id: Optional[str] = None) -> None:
    f"""{FUNCTION_DESCRIPTION}

    :param solution_id:
    :param new_solution_external_id:
    :return:
    """
    from sync_module.tools.compatibilization import (
        make_solution_compatible,
    )
    from sync_module.mi.config import MapsIndoors, Settings, set_settings
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

    _logger.info(f"Running compatiblisation on {solution_id=}")

    solution_external_id = None
    if new_solution_external_id:
        solution_external_id = new_solution_external_id

    compatibility_report = make_solution_compatible(
        solution_id, new_external_id=solution_external_id
    )

    from qgis.PyQt import QtWidgets

    formatted_report = indent(("\n".join(compatibility_report)), "  - ")
    QtWidgets.QMessageBox.information(
        None,
        "Compatiblity Report",
        f"Compatibilised Solution {solution_id}:\n{formatted_report}",
    )

    _logger.info(f"Finished compatiblisation on {solution_id=}")


if __name__ == "__main__":

    def asijdauh():
        kemper_qgis = "4b2592bdd05342f2ada9cca3"

        run(solution_id=kemper_qgis)

    asijdauh()
