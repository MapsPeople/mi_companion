#!/usr/bin/python
import logging
from typing import Optional

from mi_plugin import DEFAULT_PLUGIN_SETTINGS, PROJECT_NAME, RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]
FUNCTION_DESCRIPTION = """Sends a request to the furniture detection.
"""
# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QMessageBox, QProgressBar, QApplication, QLabel
# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, QtCore, uic
# noinspection PyUnresolvedReferences
from qgis.core import QgsMessageLog
# noinspection PyUnresolvedReferences
from qgis.utils import iface

# Global references to keep objects alive during processing
_worker = None
_thread = None
_progress_bar = None
_status_label = None


class Worker(QtCore.QObject):
    # Signal that will be emitted when the task is completed
    task_completed = QtCore.pyqtSignal()
    # Signal to report progress (0-100)
    progress_updated = QtCore.pyqtSignal(int)

    def furniture_detection_run(self):
        """
        'furniture-detection-run' implementation
        Performs furniture detection processing in a separate thread
        """
        # This will run in a separate thread
        import time

        logger.warning("Starting furniture detection task...")

        # Get the currently selected layer in QGIS
        selected_layer = iface.activeLayer()

        if selected_layer is None:
            logger.error("No layer selected in QGIS")
            self.task_completed.emit()
            return

        # Get basic layer information
        layer_name = selected_layer.name()
        layer_source = selected_layer.source()

        logger.warning(f"Layer name: {layer_name}")
        logger.warning(f"Layer source: {layer_source}")

        if '|layername=' in layer_source:
            # Extract the file path part and layer name more reliably
            file_path = layer_source.split('|')[0]
            # Get the layer name from the source string
            for param in layer_source.split('|')[1:]:
                if param.startswith('layername='):
                    sqlite_layer_name = param.replace('layername=', '')
                    break

            # Now check if it's actually a SQLite file
            is_sqlite = file_path.lower().endswith('.sqlite')

            if is_sqlite:
                logger.warning(f"This is a SQLite layer with file: {file_path}")
                logger.warning(f"SQLite internal layer name: {sqlite_layer_name}")

                # Check if it's the specific layer we're looking for
                if sqlite_layer_name == 'cad_3857':
                    logger.warning("This is the cad_3857 layer we're looking for!")
                else:
                    logger.warning("This is not the cad_3857 layer we're looking for!")
                    return
            else:
                logger.warning("This is not a SQLite layer")
                return
        else:
            logger.warning("This is not a SQLite layer")
            return

        # Simulate work with progress updates
        steps = 10
        for step in range(steps):
            # Your furniture detection code using layer_source_path goes here
            time.sleep(1)  # Each step takes 1 second in this example

            # Calculate progress percentage and emit signal
            progress = int((step + 1) / steps * 100)
            self.progress_updated.emit(progress)

        logger.warning("Furniture detection task completed")
        # Emit signal when done
        self.task_completed.emit()


def setup_status_bar_progress():
    """Set up a progress bar in the QGIS status bar"""
    global _progress_bar, _status_label

    # Create status label
    _status_label = QLabel("Detecting furniture: ")

    # Create progress bar with fixed width
    _progress_bar = QProgressBar()
    _progress_bar.setMinimum(0)
    _progress_bar.setMaximum(100)
    _progress_bar.setValue(0)
    _progress_bar.setFixedWidth(150)  # Set a fixed width to avoid taking too much space

    # Add widgets to QGIS status bar using the correct approach
    # The QGIS status bar is a standard QStatusBar
    status_bar = iface.mainWindow().statusBar()
    status_bar.addWidget(_status_label)
    status_bar.addWidget(_progress_bar)


def cleanup_status_bar_progress():
    """Remove progress bar from status bar when task is completed"""
    global _progress_bar, _status_label

    if _progress_bar or _status_label:
        # Get the status bar
        status_bar = iface.mainWindow().statusBar()

        if _progress_bar:
            status_bar.removeWidget(_progress_bar)
            _progress_bar.deleteLater()
            _progress_bar = None

        if _status_label:
            status_bar.removeWidget(_status_label)
            _status_label.deleteLater()
            _status_label = None


def update_progress(value):
    """Update the progress bar with the current progress value"""
    if _progress_bar:
        _progress_bar.setValue(value)


def show_completion():
    """Show completion message and clean up"""
    global _worker, _thread

    # Clean up status bar widgets
    cleanup_status_bar_progress()

    # Show completion message
    QtWidgets.QMessageBox.information(
        iface.mainWindow(),
        "Furniture Detection Completed",
        "Furniture detection has been completed successfully!"
    )

    # Clear references to allow cleanup
    _worker = None
    _thread = None


def run() -> None:
    """
    Run furniture detection on the selected layer
    """
    global _worker, _thread
    logger.warning("Blaaaaaaaaaaaaaaaabla")
    # If there's already a thread running, don't start another one
    if _thread is not None and _thread.isRunning():
        QtWidgets.QMessageBox.warning(
            iface.mainWindow(),
            "Task Already Running",
            "Furniture detection is already running. Please wait until it completes."
        )
        return

    # Add progress bar to status bar
    setup_status_bar_progress()

    # Create worker
    _worker = Worker()

    # Create thread
    _thread = QtCore.QThread()

    # Move worker to thread
    _worker.moveToThread(_thread)

    # Connect signals for progress updates
    _worker.progress_updated.connect(update_progress)

    # Connect signals for task completion
    _worker.task_completed.connect(show_completion)

    # Setup thread start/stop - using the furniture_detection_run method
    _thread.started.connect(_worker.furniture_detection_run)
    _worker.task_completed.connect(_thread.quit)

    # Setup cleanup connections
    _thread.finished.connect(_thread.deleteLater)
    _worker.task_completed.connect(_worker.deleteLater)

    # Start thread
    logger.info("Starting furniture detection thread")
    _thread.start()