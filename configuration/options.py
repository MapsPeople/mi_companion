# !/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "heider"
__doc__ = r"""
            TODO: Extract qlive specific code from this file.
           Created on 5/5/22
           """

__all__ = [
    "QliveOptionsPage",
    "QliveOptionsPageFactory",
]

import json
from itertools import count
from typing import Mapping

from jord.qgis_utilities import reconnect_signal

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QHBoxLayout

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

# noinspection PyUnresolvedReferences
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory

from .project_settings import DEFAULT_PROJECT_SETTINGS, ZeroMQProtocol
from .settings import (
    restore_default_project_settings,
    store_project_setting,
    read_project_setting,
    ensure_json_quotes,
)
from ..constants import PROJECT_NAME, VERSION
from ..utilities import resolve_path, get_icon_path, load_icon

QGIS_PROJECT = QgsProject.instance()
VERBOSE = False

OptionWidget, OptionWidgetBase = uic.loadUiType(resolve_path("options.ui", __file__))


class QliveOptionsPageFactory(QgsOptionsWidgetFactory):
    def __init__(self):
        super().__init__()

    def icon(self):
        return load_icon("qlive.png")

    def createWidget(self, parent):
        return QliveOptionsPage(parent)


class QliveOptionsWidget(OptionWidgetBase, OptionWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.icon_label.setPixmap(QtGui.QPixmap(get_icon_path("qlive.png")))
        self.title_label.setText(f"{PROJECT_NAME}")
        self.sponsor_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))
        self.version_label.setText(f"{VERSION}")

        reconnect_signal(self.refresh_button.clicked, self.on_refresh_button_clicked)
        reconnect_signal(
            self.server_reset_button.clicked, self.on_server_reset_button_clicked
        )
        reconnect_signal(
            self.category_reset_button.clicked, self.on_server_reset_button_clicked
        )
        reconnect_signal(self.server_apply_button.clicked, self.on_server_apply)
        reconnect_signal(
            self.apply_category_mapping_button.clicked, self.on_apply_category_mapping
        )

        self.reload_settings()

        reconnect_signal(
            self.auto_start_server_check_box.stateChanged,
            self.on_auto_start_server_changed,
        )

        self.server_status_label.setText(
            ""
        )  # TODO: make status something like "Port: 5555" if server is runnnig else "Not Running"

    def on_auto_start_server_changed(self, state) -> None:
        """

        :param state:
        :return:None
        :rtype: None
        """
        store_project_setting("AUTO_START_SERVER", state, project_name=PROJECT_NAME)

    def reload_settings(self, load_attempts: int = 2) -> None:
        for a in range(load_attempts):
            try:
                self.port_spin_box.setValue(
                    int(
                        read_project_setting(
                            "SERVER_PORT",
                            defaults=DEFAULT_PROJECT_SETTINGS,
                            project_name=PROJECT_NAME,
                        )
                    )
                )

                self.port_increments_spin_box.setValue(
                    int(
                        read_project_setting(
                            "SERVER_PORT_INCREMENTS",
                            defaults=DEFAULT_PROJECT_SETTINGS,
                            project_name=PROJECT_NAME,
                        )
                    )
                )

                self.protocol_combo_box.clear()
                self.protocol_mapping = {
                    v: p.value for v, p in zip(count(), ZeroMQProtocol)
                }
                self.protocol_combo_box.addItems(list(self.protocol_mapping.values()))
                current_protocol = str(
                    ZeroMQProtocol(
                        eval(
                            read_project_setting(
                                "SERVER_PROTOCOL",
                                defaults=DEFAULT_PROJECT_SETTINGS,
                                project_name=PROJECT_NAME,
                            )
                        )
                    ).value
                )
                current_protocol_idx = {p: v for v, p in self.protocol_mapping.items()}
                self.protocol_combo_box.setCurrentIndex(
                    int(current_protocol_idx[current_protocol])
                )
                self.protocol_combo_box.setEditable(False)
                reconnect_signal(
                    self.protocol_combo_box.currentTextChanged,
                    self.on_protocol_combo_box_changed,
                )

                self.categorisation_text_edit.setPlainText(
                    json.dumps(
                        eval(
                            read_project_setting(
                                "DEFAULT_CLASSIFY_MAPPING",
                                defaults=DEFAULT_PROJECT_SETTINGS,
                                project_name=PROJECT_NAME,
                            )
                        ),
                        indent=int(
                            read_project_setting(
                                "JSON_INDENT",
                                defaults=DEFAULT_PROJECT_SETTINGS,
                                project_name=PROJECT_NAME,
                            )
                        ),
                    )
                )

                return  # success return
            except Exception as e:
                # if a > load_attempts - 1:
                raise e

                restore_default_project_settings()

    def on_protocol_combo_box_changed(self, value):
        # store_project_setting("SERVER_PROTOCOL",                          ZeroMQProtocol(self.protocol_combo_box.currentText()),                          project_name=PROJECT_NAME)
        if value:
            s = ZeroMQProtocol(value)
            store_project_setting("SERVER_PROTOCOL", s, project_name=PROJECT_NAME)

    def on_apply_category_mapping(self):
        text = self.categorisation_text_edit.toPlainText()
        if text is None or text == "":
            text = "{}"

        mapping = json.loads(ensure_json_quotes(text))

        assert isinstance(mapping, Mapping)

        store_project_setting(
            "DEFAULT_CLASSIFY_MAPPING", mapping, project_name=PROJECT_NAME
        )

    def on_server_apply(self):
        store_project_setting(
            "SERVER_PORT", int(self.port_spin_box.value()), project_name=PROJECT_NAME
        )

        store_project_setting(
            "SERVER_PORT_INCREMENTS",
            int(self.port_increments_spin_box.value()),
            project_name=PROJECT_NAME,
        )

    def on_server_reset_button_clicked(self):
        restore_default_project_settings()
        self.reload_settings()

    def on_refresh_button_clicked(self):
        ...

    def populate_settings(self):
        from qgis.core import QgsSettings

        qs = QgsSettings()

        for k in sorted(qs.allKeys()):
            print(k)

        # self.settings_tree_view
        # self.export_settings_button
        # self.import_settings_button
        # self.settings_file_widget


class QliveOptionsPage(QgsOptionsPageWidget):
    def __init__(self, parent):
        super().__init__(parent)
        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.options_widget = QliveOptionsWidget()
        root_layout.addWidget(self.options_widget)

        self.setLayout(root_layout)

    def apply(self):
        pass
