from logging import warning
from typing import Optional, Mapping, Any

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

from qlive.qlive import PROJECT_NAME
from qlive.qlive.configuration.project_settings import DEFAULT_PROJECT_SETTINGS

VERBOSE = False
QGIS_PROJECT = QgsProject.instance()


def restore_default_project_settings(
    defaults: Optional[Mapping] = DEFAULT_PROJECT_SETTINGS,
    *,
    project_name: str = PROJECT_NAME,
    verbose: bool = VERBOSE,
) -> None:
    if defaults is None:
        defaults = {}
    for key, value in defaults.items():
        store_project_setting(key, value, project_name=project_name, verbose=verbose)


def store_project_setting(
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

    if verbose:
        print("stored: ", project_name, key, value)


def read_project_setting(
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

    if verbose:
        print("read: ", project_name, key, val)
        if not type_conversion_ok:
            warning(f"read_plugin_setting: {key} {val} {type_conversion_ok}")

    return val


def ensure_json_quotes(json_str: str) -> str:
    return json_str.replace("'", '"').rstrip('"').lstrip('"')
