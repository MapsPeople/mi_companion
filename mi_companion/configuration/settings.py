import logging
from typing import Dict, Optional, Mapping, Any

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject
from qlive.qlive import PROJECT_NAME
from qlive.qlive.configuration.project_settings import DEFAULT_PROJECT_SETTINGS

VERBOSE = True
QGIS_PROJECT = QgsProject.instance()
LOGGER = logging.getLogger(__name__)


def restore_default_plugin_settings(
    defaults: Optional[Mapping] = DEFAULT_PROJECT_SETTINGS,
    *,
    project_name: str = PROJECT_NAME,
    verbose: bool = VERBOSE,
) -> None:
    if defaults is None:
        defaults = {}

    for key, value in defaults.items():
        embedded_store_plugin_setting(
            key, value, project_name=project_name, verbose=verbose
        )


def list_project_settings() -> Dict[str, Any]:
    # return QGIS_PROJECT.customVariables()
    # from qgis.core import QgsExpressionContextUtils

    # keys = QgsExpressionContextUtils.projectScope(QGIS_PROJECT).variableNames()

    # return {k: read_project_setting(k) for k in keys}
    # QGIS_PROJECT
    return None


def embedded_store_plugin_setting(
    key: str, value: Any, *, project_name: str = PROJECT_NAME, verbose: bool = VERBOSE
) -> None:
    if isinstance(value, bool):
        QGIS_PROJECT.writeEntryBool(project_name, key, value)
    elif isinstance(value, float):
        QGIS_PROJECT.writeEntryDouble(project_name, key, value)
    # elif isinstance(value, int): # DOES NOT EXIST!
    #    qgis_project.writeEntryNum(project_name, key, value)
    else:
        value = str(value)
        QGIS_PROJECT.writeEntry(project_name, key, value)

    # jord.qgis_utilities.store_plugin_setting()

    if verbose:
        print("stored: ", project_name, key, value)


def embedded_read_plugin_setting(
    key: str,
    type_hint: type = None,
    *,
    defaults: Mapping = None,
    project_name: str = PROJECT_NAME,
    verbose: bool = VERBOSE,
) -> Any:
    # read values (returns a tuple with the value, and a status boolean
    # which communicates whether the value retrieved could be converted to
    # its type, in these cases a string, an integer, a double and a boolean
    # respectively)

    if defaults is None:
        defaults = {}

    if type_hint is not None:
        if type_hint is bool:
            val, type_conversion_ok = QGIS_PROJECT.readBoolEntry(
                project_name, key, defaults.get(key, None)
            )
        elif type_hint is float:
            val, type_conversion_ok = QGIS_PROJECT.readDoubleEntry(
                project_name, key, defaults.get(key, None)
            )
        elif type_hint is int:
            val, type_conversion_ok = QGIS_PROJECT.readNumEntry(
                project_name, key, defaults.get(key, None)
            )
        else:
            val, type_conversion_ok = QGIS_PROJECT.readEntry(
                project_name, key, str(defaults.get(key, None))
            )
    else:
        val, type_conversion_ok = QGIS_PROJECT.readEntry(
            project_name, key, str(defaults.get(key, None))
        )

    if type_hint is not None:
        val = type_hint(val)

    # jord.qgis_utilities.read_plugin_setting()

    if verbose:
        print("read: ", project_name, key, val)
        if not type_conversion_ok:
            LOGGER.warning(f"read_plugin_setting: {key} {val} {type_conversion_ok}")

    return val


def ensure_json_quotes(json_str: str) -> str:
    return json_str.replace("'", '"').rstrip('"').lstrip('"')
