# !/usr/bin/env python3


__author__ = "heider"
__doc__ = r"""
            TODO: Extract qlive specific code from this file.
           Created on 5/5/22
           """

__all__ = [
    "DeploymentCompanionOptionsPage",
    "DeploymentOptionsPageFactory",
]


import logging

from jord.qgis_utilities import read_plugin_setting, store_plugin_setting
from jord.qgis_utilities.helpers import reconnect_signal

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QHBoxLayout

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

# noinspection PyUnresolvedReferences
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory

from .project_settings import DEFAULT_PLUGIN_SETTINGS
from ..constants import PROJECT_NAME, VERSION
from ..utilities.paths import resolve_path, get_icon_path, load_icon

QGIS_PROJECT = QgsProject.instance()
VERBOSE = False

LOGGER = logging.getLogger(__name__)

OptionWidget, OptionWidgetBase = uic.loadUiType(resolve_path("options.ui", __file__))


class DeploymentOptionsPageFactory(QgsOptionsWidgetFactory):
    def __init__(self):
        super().__init__()

    # noinspection PyMethodMayBeStatic
    def icon(self):
        return load_icon("mp_notext.png")

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def createWidget(self, parent):
        return DeploymentCompanionOptionsPage(parent)


def reload_settings(load_attempts: int = 2) -> None:
    for a in range(load_attempts):
        try:
            return  # success return
        except Exception as e:
            # if a > load_attempts - 1:
            raise e

            # restore_default_project_settings()


class DeploymentCompanionOptionsWidget(OptionWidgetBase, OptionWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.icon_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))
        self.version_label.setText(f"{VERSION}")

        self.settings_list_model = None
        self.type_map = None
        reload_settings()
        self.populate_settings()

    def populate_settings(self):
        # from qgis.core import QgsSettings
        # noinspection PyUnresolvedReferences
        from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
        from qgis.PyQt import QtCore

        # qs = QgsSettings()
        # setting_keys = qs.allKeys()
        # setting_keys = list_project_settings()

        if hasattr(self, "settings_list_model"):
            del self.settings_list_model

        self.settings_list_model = QStandardItemModel(self.settings_tree_view)
        self.type_map = {}

        for k in sorted(DEFAULT_PLUGIN_SETTINGS.keys()):
            #   q = qs.getValue(k, None)  # DEFAULT_PROJECT_SETTINGS[k])
            q = read_plugin_setting(
                k,
                project_name=PROJECT_NAME,
                default_value=DEFAULT_PLUGIN_SETTINGS[k],
            )

            name_item = QStandardItem(k)
            name_item.setEditable(False)

            state_item = QStandardItem(str(q))
            state_item.setDragEnabled(False)

            self.type_map[k] = type(q)

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
            self.settings_list_model.setHeaderData(ci, QtCore.Qt.Horizontal, str(label))

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

    def setting_item_changed(self, item):  #: PyQt5.QtGui.QStandardItem
        try:
            key = self.settings_list_model.item(item.row(), 0).text()
            value = self.type_map[key](item.text())
            store_plugin_setting(key, value, project_name=PROJECT_NAME)
        except Exception as e:
            LOGGER.warning(e)


class DeploymentCompanionOptionsPage(QgsOptionsPageWidget):
    def __init__(self, parent):
        super().__init__(parent)
        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.options_widget = DeploymentCompanionOptionsWidget()
        root_layout.addWidget(self.options_widget)

        self.setLayout(root_layout)

    def apply(self):
        pass
