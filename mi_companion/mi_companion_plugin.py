"""
mi_companion

                             -------------------
       begin                : 2023-03-03
       git sha              : $Format:%H$
       copyright            : (C) 2022 by MapsPeople
       email                : chen@mapspeople.com

"""

import logging
from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtGui import QIcon

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QAction

# noinspection PyUnresolvedReferences
from qgis.core import QgsSettings

from .constants import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME

logger = logging.getLogger(__name__)

# my_plugin = qgis.utils.plugins['MapsIndoors Beta']

try:
    from jord.qt_utilities import DockWidgetAreaFlag
    from jord.qgis_utilities.helpers import signals
    from jord.qgis_utilities import read_plugin_setting

    from .configuration.options import DeploymentOptionsPageFactory
    from .gui.main_dock import MapsIndoorsCompanionDockWidget

    # noinspection PyUnresolvedReferences
    from .resources import *  # Initialize Qt resources from file resources.py

    assert qt_resource_data is not None  # from resources.py

except ModuleNotFoundError as e1:
    try:  # TODO MAYbe fetch eqips implementation, # otherwise assume warg was installed during bootstrap
        # from warg import get_requirements_from_file
        if False:  # TODO: Only do this if bundle was not found
            from warg.packages import install_requirements_from_file

            install_requirements_from_file(Path(__file__).parent / "requirements.txt")

        from jord.qt_utilities import DockWidgetAreaFlag
        from jord.qgis_utilities.helpers import signals
        from jord.qgis_utilities import read_plugin_setting

        from .configuration.options import DeploymentOptionsPageFactory
        from .gui.main_dock import MapsIndoorsCompanionDockWidget

        # noinspection PyUnresolvedReferences
        from .resources import *  # Initialize Qt resources from file resources.py

        assert qt_resource_data is not None  # from resources.py

    except ModuleNotFoundError as e2:
        logger.warning(f"{e2}")
        raise e1

MENU_INSTANCE_NAME = f"&{PROJECT_NAME.lower()}"

VERBOSE = False
DEBUGGING = False
FORCE_RELOAD = False


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

        _ = """        if False:
            import pydevd_pycharm

            pydevd_pycharm.settrace(
                "localhost",
                port=6969,
                stdoutToServer=True,
                stderrToServer=True,
            )
"""

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
            logger.warning(
                f"Unable to determine locale for {PROJECT_NAME} was {str(type(locale))} {str(locale)}"
            )

        self.open_server_dock_window_action = None
        self.mi_companion_dock_widget = None

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
    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.options_factory.setTitle(self.tr(PROJECT_NAME))
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        resource_path = read_plugin_setting(
            "RESOURCES_BASE_PATH",
            default_value=DEFAULT_PLUGIN_SETTINGS["RESOURCES_BASE_PATH"],
            project_name=PROJECT_NAME,
        )
        self.open_server_dock_window_action = QAction(
            QIcon(f"{resource_path}/icons/mp_notext.png"),
            self.tr(PROJECT_NAME),
            self.iface.mainWindow(),
        )

        self.actions.append(self.open_server_dock_window_action)

        signals.reconnect_signal(
            self.open_server_dock_window_action.triggered, self.open_dock_widget
        )

        self.iface.addToolBarIcon(self.open_server_dock_window_action)

        self.first_start = True  # will be set False in run()

    def open_dock_widget(self) -> None:
        """
        Opens the dock
        """
        if self.mi_companion_dock_widget is None:
            self.mi_companion_dock_widget = MapsIndoorsCompanionDockWidget(self.iface)

            signals.reconnect_signal(
                self.mi_companion_dock_widget.plugin_closing,
                self.on_dock_widget_closed,
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
                self.mi_companion_dock_widget,
            )

    def on_dock_widget_closed(self) -> None:  # used when Dock dialogue is closed
        """
        Gets called when the dock is closed
        All the clean-up of the dock has to be done here
        """
        self.mi_companion_dock_widget = None

    def unload(self) -> None:
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(PROJECT_NAME), action)
            self.iface.removeToolBarIcon(action)
