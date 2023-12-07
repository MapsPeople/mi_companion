# -*- coding: utf-8 -*-

from pathlib import Path

from jord.qt_utilities import DockWidgetAreaFlag
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsSettings

from . import PROJECT_NAME
from .configuration.options import DeploymentOptionsPageFactory
from .configuration.project_settings import DEFAULT_PROJECT_SETTINGS
from .configuration.settings import read_project_setting
from .gui.dock_widget import GdsCompanionDockWidget
from jord.qgis_utilities.helpers import signals

# noinspection PyUnresolvedReferences
from .resources import *  # Initialize Qt resources from file resources.py

assert qt_version

MENU_INSTANCE_NAME = f"&{PROJECT_NAME.lower()}"
VERBOSE = False
DEBUGGING = False
FORCE_RELOAD = False


class GdsCompanion:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        self.iface = iface

        if False:
            import pydevd_pycharm

            pydevd_pycharm.settrace(
                "localhost",
                port=6969,
                stdoutToServer=True,
                stderrToServer=True,
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
            warnings.warn(
                f"Unable to determine locale for {PROJECT_NAME} was {str(type(locale))} {str(locale)}"
            )

        self.open_server_dock_window_action = None
        self.gds_companion_dock_widget = None

        self.options_factory = DeploymentOptionsPageFactory()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(f"&{MENU_INSTANCE_NAME}")

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
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.options_factory.setTitle(self.tr(PROJECT_NAME))
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        resource_path = read_project_setting(
            "RESOURCES_BASE_PATH",
            defaults=DEFAULT_PROJECT_SETTINGS,
            project_name=PROJECT_NAME,
        )
        self.open_server_dock_window_action = QAction(
            QIcon(f"{resource_path}/icons/mp_notext.png"),
            self.tr(PROJECT_NAME),
            self.iface.mainWindow(),
        )

        signals.reconnect_signal(
            self.open_server_dock_window_action.triggered, self.open_dock_widget
        )

        self.iface.addToolBarIcon(self.open_server_dock_window_action)

        self.first_start = True  # will be set False in run()

    def open_dock_widget(self):
        """
        Opens the dock
        """
        if self.gds_companion_dock_widget is None:
            self.gds_companion_dock_widget = GdsCompanionDockWidget(self.iface)
            signals.reconnect_signal(
                self.gds_companion_dock_widget.plugin_closing,
                self.on_dock_widget_closed,
            )
            self.iface.addDockWidget(
                DockWidgetAreaFlag(
                    eval(
                        read_project_setting(
                            "DEFAULT_WIDGET_AREA",
                            defaults=DEFAULT_PROJECT_SETTINGS,
                            project_name=PROJECT_NAME,
                        )
                    )
                ).value,
                self.gds_companion_dock_widget,
            )

    def on_dock_widget_closed(self):  # used when Dock dialog is closed
        """
        Gets called when the dock is closed
        All the cleanup of the dock has to be done here
        """
        self.gds_companion_dock_widget = None

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(PROJECT_NAME), action)
            self.iface.removeToolBarIcon(action)
