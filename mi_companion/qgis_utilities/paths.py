import os
from pathlib import Path
from typing import Mapping, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtGui import QIcon
from warg import passes_kws_to

from ..constants import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME

__all__ = ["resolve_path", "load_icon", "get_icon_path"]


def resolve_path(path: str, base_path: Optional[Path] = None) -> str:
    """


    :param path:
    :param base_path:
    :return:
    """
    if not base_path:
        base_path = Path(os.path.realpath(__file__)).parent.parent.parent

    base_path = Path(base_path)

    if base_path.is_file():
        base_path = base_path.parent

    return str(base_path / path)


def get_icon_path(
    icon_file_name: str,
    defaults: Mapping = DEFAULT_PLUGIN_SETTINGS,
    project_name: str = PROJECT_NAME,
) -> str:
    """

    :param icon_file_name:
    :param defaults:
    :param project_name:
    :return:
    """
    from jord.qgis_utilities import read_plugin_setting

    resource_path = read_plugin_setting(
        "RESOURCES_BASE_PATH",
        default_value=defaults["RESOURCES_BASE_PATH"],
        project_name=project_name,
    )
    return f"{resource_path}/icons/{icon_file_name}"


@passes_kws_to(get_icon_path)
def load_icon(*args, **kwargs) -> QIcon:
    """

    :param args:
    :param kwargs:
    :return:
    """
    icon = QIcon(get_icon_path(*args, **kwargs))

    if icon.isNull():
        # Returns true if this is a null pixmap; otherwise returns false .
        # A null pixmap has zero width, zero height and no contents. You cannot draw in a null pixmap.
        print("Did not find icon")

    return icon
