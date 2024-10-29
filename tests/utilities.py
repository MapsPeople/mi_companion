"""Common functionality used by regression tests."""

import logging
import os
import sys
from typing import Tuple

logger = logging.getLogger("QGIS")

QGIS_APP = None  # Static variable used to hold handle to running QGIS app
CANVAS = None
PARENT = None
IFACE = None


def get_qgis_app() -> None:
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsApplication

    # supply path to qgis install location
    QgsApplication.setPrefixPath("/usr", True)

    # create a reference to the QgsApplication, setting the
    # second argument to False disables the GUI
    qgs = QgsApplication([], False)

    # load providers
    qgs.initQgis()

    print("I ran")

    # qgs.exitQgis()


def get_qgis_app_crashing(cleanup: bool = True) -> Tuple:
    """Start one QGIS application to test against.

    :returns: Handle to QGIS app, canvas, iface and parent. If there are any
        errors the tuple members will be returned as None.
    :rtype: (QgsApplication, CANVAS, IFACE, PARENT)

    If QGIS is already running the handle to that app will be returned.
    """

    # noinspection PyUnresolvedReferences
    from qgis.core import QgsApplication

    # noinspection PyUnresolvedReferences
    from qgis.PyQt.QtCore import QSize

    # noinspection PyUnresolvedReferences
    from qgis.PyQt.QtWidgets import QWidget

    # noinspection PyUnresolvedReferences
    from qgis.gui import QgsMapCanvas

    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    from .qgis_interface import QgisInterface

    import atexit

    global QGIS_APP, PARENT, IFACE, CANVAS  # pylint: disable=W0603

    if iface:
        QGIS_APP = QgsApplication
        CANVAS = iface.mapCanvas()
        PARENT = iface.mainWindow()
        IFACE = iface
        return QGIS_APP, CANVAS, IFACE, PARENT

    try:
        QGIS_APP  # pylint: disable=used-before-assignment
    except NameError:
        my_gui_flag = True  # All test will run qgis in gui mode

        # In python3 we need to convert to a bytes object (or should
        # QgsApplication accept a QString instead of const char* ?)
        try:
            argv_bytes = list(map(os.fsencode, sys.argv))
        except AttributeError:
            argv_bytes = sys.argv

        # supply path to qgis install location
        QgsApplication.setPrefixPath("/usr", True)

        # Note: QGIS_PREFIX_PATH is evaluated in QgsApplication -
        # no need to mess with it here.
        QGIS_APP = QgsApplication(argv_bytes, my_gui_flag)

        QGIS_APP.initQgis()
        logger.debug(QGIS_APP.showSettings())

        def debug_log_message(message, tag, level):
            """
            Prints a debug message to a log
            :param message: message to print
            :param tag: log tag
            :param level: log message level (severity)
            :return:
            """
            print(f"{tag}({level}): {message}")

        QgsApplication.instance().messageLog().messageReceived.connect(
            debug_log_message
        )

        if cleanup:

            @atexit.register
            def exitQgis():  # pylint: disable=unused-variable
                """
                Gracefully closes the QgsApplication instance
                """
                try:
                    # pylint: disable=used-before-assignment
                    # pylint: disable=redefined-outer-name
                    QGIS_APP.exitQgis()  # noqa
                    QGIS_APP = None  # noqa
                    # pylint: enable=used-before-assignment
                    # pylint: enable=redefined-outer-name
                except NameError:
                    pass

    if PARENT is None:
        # noinspection PyPep8Naming
        PARENT = QWidget()

    if CANVAS is None:
        # noinspection PyPep8Naming
        CANVAS = QgsMapCanvas(PARENT)
        CANVAS.resize(QSize(400, 400))

    if IFACE is None:
        # QgisInterface is a stub implementation of the QGIS plugin interface
        # noinspection PyPep8Naming
        IFACE = QgisInterface(CANVAS)

    return QGIS_APP, CANVAS, IFACE, PARENT
