# !/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "heider"
__doc__ = r"""
            TODO: Extract qlive specific code from this file.
           Created on 5/5/22
           """

__all__ = [
    "DeploymentCompanionOptionsPage",
    "DeploymentOptionsPageFactory",
]

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QHBoxLayout

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

# noinspection PyUnresolvedReferences
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory

from .settings import (
    restore_default_project_settings,
)
from ..constants import PROJECT_NAME, VERSION
from ..utilities.paths import resolve_path, get_icon_path, load_icon

QGIS_PROJECT = QgsProject.instance()
VERBOSE = False

OptionWidget, OptionWidgetBase = uic.loadUiType(resolve_path("options.ui", __file__))


class DeploymentOptionsPageFactory(QgsOptionsWidgetFactory):
    def __init__(self):
        super().__init__()

    def icon(self):
        return load_icon("mp_notext.png")

    def createWidget(self, parent):
        return DeploymentCompanionOptionsPage(parent)


class DeploymentCompanionOptionsWidget(OptionWidgetBase, OptionWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.icon_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))
        self.title_label.setText(f"{PROJECT_NAME}")
        self.sponsor_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))
        self.version_label.setText(f"{VERSION}")

        self.reload_settings()
        self.populate_settings()

    def reload_settings(self, load_attempts: int = 2) -> None:
        for a in range(load_attempts):
            try:
                return  # success return
            except Exception as e:
                # if a > load_attempts - 1:
                raise e

                restore_default_project_settings()

    def populate_settings(self):
        from qgis.core import QgsSettings

        qs = QgsSettings()

        if False:
            for k in sorted(qs.allKeys()):
                print(k)

        # self.settings_tree_view
        # self.export_settings_button
        # self.import_settings_button
        # self.settings_file_widget


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
