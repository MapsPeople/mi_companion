"""
mi_companion

                             -------------------
       begin                : 2023-03-03
       git sha              : $Format:%H$
       copyright            : (C) 2022 by MapsPeople
       email                : chen@mapspeople.com

"""

from pathlib import Path

import logging
from functools import partial
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsSettings

from jord.qgis_utilities import read_plugin_setting, signals
from jord.qt_utilities import DockWidgetAreaFlag
from .configuration.options import DeploymentOptionsPageFactory
from .constants import (
    DEBUGGING,
    DEFAULT_PLUGIN_SETTINGS,
    MI_MENU_INSTANCE_NAME,
    PROJECT_NAME,
)
from .gui.split_widgets.digitisation_dock import DigitisationWidget
from .gui.split_widgets.export_dock import ExportWidget
from .gui.split_widgets.import_dock import ImportWidget
from .gui.split_widgets.tools_dock import EntryPointsWidget
from .resources import *  # Initialize Qt resources from file resources.py

assert qt_resource_data is not None  # from resources.py

_logger = logging.getLogger(__name__)


class MapsIndoorsCompanionPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        self.iface = iface

        if DEBUGGING:
            try:
                if False:
                    # import pydevd_pycharm

                    # pydevd_pycharm.settrace(
                    #    "localhost",
                    #    port=6969,
                    #    stdoutToServer=True,
                    #    stderrToServer=True,
                    # )
                    _logger.warrning(
                        "Debugging was enabled, pydevd_pycharm is available on port 6969"
                    )
            except:
                _logger.error(
                    "Debugging was enabled but pydevd_pycharm was not found, no debugging server was started"
                )

        self.plugin_dir = Path(__file__).parent
        locale = QgsSettings().value(
            f"{PROJECT_NAME}/locale/userLocale", QLocale().name()
        )
        if isinstance(locale, str):
            locale_path = self.plugin_dir / "i18n" / f"{PROJECT_NAME}_localeSDAUIH.qm"

            if locale_path.exists():
                self.translator = QTranslator()
                self.translator.load(str(locale_path))
                QCoreApplication.installTranslator(self.translator)
        else:
            _logger.warning(
                f"Unable to determine locale for {PROJECT_NAME} was {str(type(locale))} {str(locale)}"
            )

        self.open_monolith_dock_window_action = None
        self.mi_companion_monolith_dock_widget = None

        self.options_factory = DeploymentOptionsPageFactory()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(f"&{MI_MENU_INSTANCE_NAME}")

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: Str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(PROJECT_NAME, message)

    # noinspection PyPep8Naming
    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.options_factory.setTitle(self.tr(PROJECT_NAME))
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        resource_path = read_plugin_setting(
            "RESOURCES_BASE_PATH",
            default_value=DEFAULT_PLUGIN_SETTINGS["RESOURCES_BASE_PATH"],
            project_name=PROJECT_NAME,
        )

        self.common_widget_actions = []

        for label, dock_cls, icon in (
            (
                ImportWidget.menu_name,
                ImportWidget,
                QIcon(f"{resource_path}/icons/arrow_down.png"),
            ),
            (
                DigitisationWidget.menu_name,
                DigitisationWidget,
                QIcon(f"{resource_path}/icons/mp_notext.png"),
            ),
            (
                ExportWidget.menu_name,
                ExportWidget,
                QIcon(f"{resource_path}/icons/arrow_up.png"),
            ),
            (
                EntryPointsWidget.menu_name,
                EntryPointsWidget,
                QIcon(f"{resource_path}/icons/ruby.png"),
            ),
        ):
            action = QAction(
                icon,
                self.tr(label),
                self.iface.mainWindow(),
            )

            signals.reconnect_signal(
                action.triggered, partial(self.open_split_dock_widget, dock_cls)
            )
            self.iface.addPluginToMenu(self.menu, action)
            # self.iface.addToolBarIcon(action)
            self.actions.append(action)
            if dock_cls is not EntryPointsWidget:
                self.common_widget_actions.append(action)

        if True:
            self.open_monolith_dock_window_action = QAction(
                QIcon(f"{resource_path}/icons/mp_notext.png"),
                self.tr(PROJECT_NAME),
                self.iface.mainWindow(),
            )

            self.actions.append(self.open_monolith_dock_window_action)

            signals.reconnect_signal(
                self.open_monolith_dock_window_action.triggered,
                self.open_monolith_dock_widget,
            )

            self.iface.addToolBarIcon(self.open_monolith_dock_window_action)

        self.dock_widget_instances = {}

        self.first_start = True  # will be set False in run()

    def open_split_dock_widget(self, dock_cls) -> None:
        """
        Opens a specific dock widget
        """
        name = dock_cls.__name__
        if name in self.dock_widget_instances:
            self.dock_widget_instances[name].show()
            self.dock_widget_instances[name].raise_()
            return

        widget = dock_cls(self.iface)
        self.dock_widget_instances[name] = widget

        signals.reconnect_signal(
            widget.plugin_closing,
            partial(self.on_split_dock_widget_closed, name),
        )

        a = read_plugin_setting(
            "DEFAULT_WIDGET_AREA",
            default_value=DEFAULT_PLUGIN_SETTINGS["DEFAULT_WIDGET_AREA"],
            project_name=PROJECT_NAME,
        )

        if not isinstance(a, DockWidgetAreaFlag):
            a = eval(a)  # TODO: REMOVE EVAL?

        self.iface.addDockWidget(
            DockWidgetAreaFlag(a).value,
            widget,
        )

    def on_split_dock_widget_closed(
        self, name
    ) -> None:  # used when Dock dialogue is closed
        """
        Gets called when the dock is closed
        All the clean-up of the dock has to be done here
        """
        if name in self.dock_widget_instances:
            del self.dock_widget_instances[name]

    def open_monolith_dock_widget(self) -> None:
        """
        Opens the dock
        """
        for a in self.common_widget_actions:
            a.trigger()

    def on_dock_widget_closed(self) -> None:  # used when Dock dialogue is closed
        """
        Gets called when the dock is closed
        All the clean-up of the dock has to be done here
        """
        self.mi_companion_monolith_dock_widget = None

    def unload(self) -> None:
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(PROJECT_NAME), action)
            self.iface.removeToolBarIcon(action)
