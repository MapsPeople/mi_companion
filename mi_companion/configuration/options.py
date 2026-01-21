__author__ = "heider"
__doc__ = r"""
           Created on 5/5/22
           """

__all__ = [
    "DeploymentCompanionOptionsPage",
    "DeploymentOptionsPageFactory",
    "read_bool_setting",
    "read_float_setting",
    "reload_settings",
    "MapsIndoorsOptionsWidget",
]

import logging

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtGui, QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

# noinspection PyUnresolvedReferences
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory
from typing import Any

from jord.qgis_utilities import (
    horizontal_orientation,
    read_plugin_setting,
    reconnect_signal,
    store_plugin_setting,
)
from ..constants import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME, VERSION
from ..qgis_utilities.paths import get_icon_path, load_icon, resolve_path

_logger = logging.getLogger(__name__)


class DeploymentOptionsPageFactory(QgsOptionsWidgetFactory):

    def __init__(self):
        super().__init__()

    # noinspection PyMethodMayBeStatic
    def icon(self) -> None:
        return load_icon("mp_notext.png")

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def createWidget(self, parent: Any) -> "DeploymentCompanionOptionsPage":
        return DeploymentCompanionOptionsPage(parent)


def reload_settings(load_attempts: int = 2) -> None:
    for a in range(load_attempts):
        try:
            return  # success return
        except Exception as e:
            # if a > load_attempts - 1:
            raise e

            # restore_default_project_settings()


class MapsIndoorsOptionsWidget(
    *uic.loadUiType(str(resolve_path("options.ui", __file__)))
):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.icon_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))
        self.version_label.setText(f"{VERSION}")

        self.settings_list_model = None
        self.type_map = None
        reload_settings()
        self.populate_settings()

    def populate_settings(self) -> None:
        if hasattr(self, "settings_list_model"):
            del self.settings_list_model

        self.settings_list_model = QtGui.QStandardItemModel(self.settings_tree_view)
        self.type_map = {}

        for k in sorted(DEFAULT_PLUGIN_SETTINGS.keys()):
            #   q = qs.getValue(k, None)  # DEFAULT_PROJECT_SETTINGS[k])
            q = read_plugin_setting(
                k,
                project_name=PROJECT_NAME,
                default_value=DEFAULT_PLUGIN_SETTINGS[k],
            )

            name_item = QtGui.QStandardItem(k)
            name_item.setEditable(False)

            state_item = QtGui.QStandardItem(str(q))
            state_item.setDragEnabled(False)

            self.type_map[k] = type(DEFAULT_PLUGIN_SETTINGS[k])

            self.settings_list_model.appendRow(
                [
                    name_item,
                    state_item,
                ]
            )

        column_headers = [
            "setting",
            "value",
        ]
        for ci, label in enumerate(column_headers):
            self.settings_list_model.setHeaderData(
                ci, horizontal_orientation, str(label)
            )

        reconnect_signal(
            self.settings_list_model.itemChanged, self.setting_item_changed
        )

        self.settings_tree_view.setModel(self.settings_list_model)

        for ci in range(len(column_headers)):
            self.settings_tree_view.resizeColumnToContents(ci)

        self.settings_tree_view.show()

        # self.export_settings_button
        # self.import_settings_button
        # self.settings_file_widget

    def setting_item_changed(self, item: Any) -> None:  #: qgis.PyQt.QtGui.QStandardItem
        try:
            key = self.settings_list_model.item(item.row(), 0).text()
            item_value = item.text()

            if "false" in str(item_value).lower().strip():
                value = False
            else:
                value = self.type_map[key](item_value)

            if isinstance(value, bool):
                _logger.warning(f"{key} = {value}")

            _logger.warning(
                f"Storing new setting {id(value)=} for {key}"
            )  # Only id to obscure sensitive information from logs

            store_plugin_setting(key, value, project_name=PROJECT_NAME)
        except Exception as e:
            _logger.warning(e)


def read_bool_setting(key: str) -> bool:
    v = read_plugin_setting(
        key,
        default_value=DEFAULT_PLUGIN_SETTINGS[key],
        project_name=PROJECT_NAME,
    )
    if isinstance(v, bool):
        return v

    elif isinstance(v, str):
        # logger.warning(f"Bool {key} setting was a string with the value {v}")
        if "false" in str(v).lower().strip():
            # logger.warning(f"{key} = {False}")
            return False
        else:
            # logger.warning(f"{key} = {True}")
            return True
    else:
        raise Exception(f"{v=} was invalid for bool setting")


def read_float_setting(key: str) -> float:
    v = read_plugin_setting(
        key,
        default_value=DEFAULT_PLUGIN_SETTINGS[key],
        project_name=PROJECT_NAME,
    )
    if isinstance(v, float):
        return v

    return float(v)


class DeploymentCompanionOptionsPage(QgsOptionsPageWidget):

    def __init__(self, parent: Any):
        super().__init__(parent)
        root_layout = QtWidgets.QHBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.options_widget = MapsIndoorsOptionsWidget()
        root_layout.addWidget(self.options_widget)

        self.setLayout(root_layout)

    def apply(self) -> None:
        pass
