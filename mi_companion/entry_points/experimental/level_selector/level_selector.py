import logging
import os
from pathlib import Path
from typing import Any, Iterable, Optional

from jord.qgis_utilities.helpers import signals

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import pyqtSignal

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsLayerTree,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsLayerTreeModel,
    QgsProject,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)

# noinspection PyUnresolvedReferences
from qgis.gui import QgsDockWidget

# noinspection PyUnresolvedReferences
from qgis.utils import iface
from warg import ensure_in_sys_path

from mi_companion.qgis_utilities import resolve_path

FORM_CLASS, _ = uic.loadUiType(resolve_path("level_selector.ui", __file__))

signals.IS_DEBUGGING = True
logger = logging.getLogger(__name__)
VERBOSE = False

ensure_in_sys_path(Path(__file__).parent.parent)
__all__ = []


class LevelSelectorWidget(QgsDockWidget, FORM_CLASS):
    plugin_closing = pyqtSignal()

    def __init__(self, iface_: Any, parent: Optional[Any] = None):
        """Constructor."""
        super().__init__(parent)

        self.selected_layers = None
        self.iface_ = iface_
        self.qgis_project = QgsProject.instance()

        self.plugin_dir = Path(os.path.dirname(__file__))
        self.setupUi(self)

        signals.reconnect_signal(
            iface.layerTreeView().currentLayerChanged, self.layer_selection_changed
        )

        signals.reconnect_signal(self.enable_button.clicked, self.enable_button_clicked)
        signals.reconnect_signal(self.unfold_button.clicked, self.unfold_button_clicked)

    def unfold_button_clicked(self, reload_venues: bool = True) -> None:
        # TODO: iter iface.layerTreeView()
        selected_level = str(self.solution_combo_box.currentText())

    def layer_selection_changed(self, selected_layers) -> None:
        self.level_combo_box.clear()

        if selected_layers:
            if isinstance(selected_layers, Iterable):
                self.selected_layers = selected_layers
            else:
                self.selected_layers = [selected_layers]

        unique_level_values = set()
        if len(self.selected_layers):
            self.gather_unique_levels(self.selected_layers, unique_level_values)

        self.level_combo_box.addItems(sorted(unique_level_values))

    def gather_unique_levels(self, layers, unique_level_values):
        for layer in layers:
            if isinstance(layer, QgsRasterLayer):
                ...

            elif isinstance(layer, QgsLayerTreeGroup):
                self.gather_unique_levels([layer], unique_level_values)

            elif isinstance(layer, QgsVectorLayer):
                field_names = layer.fields().names()
                col_idx = None

                if "level" in field_names:
                    col_idx = layer.fields().indexFromName("level")
                elif "floor_index" in field_names:
                    col_idx = layer.fields().indexFromName("floor_index")

                if col_idx is not None:
                    for feature in layer.getFeatures():
                        value = str(feature.attributes()[col_idx])
                        logger.error(f"Found {value}")
                        unique_level_values.add(value)

    def enable_button_clicked(self) -> None:
        ...
        # TODO: iter iface.layerTreeView()
        selected_level = str(self.solution_combo_box.currentText())

        # renderer = layer.renderer()
        # # Rescale single symbol layers
        # if renderer.type() == "singleSymbol":
        #     symbol = renderer.symbol()
        #     new_symbol = scale_symbol(scale_factor, symbol, layer_names, idx)
        #     renderer.setSymbol(new_symbol)
        #
        # # Rescale categorized symbol layers
        # elif renderer.type() == "categorizedSymbol":
        #     symbol = renderer.sourceSymbol()
        #     new_symbol = scale_symbol(scale_factor, symbol, layer_names, idx)
        #     renderer.updateSymbols(new_symbol)
        #
        # for sl in renderer.symbols(QgsRenderContext()).symbolLayers():
        #     if sl.value() == "0":
        #         sl.setEnabled(False)
        #
        # layer.triggerRepaint()
        # iface.layerTreeView().refreshLayerSymbology(layer.id())

    # noinspection PyPep8Naming
    def closeEvent(self, event) -> None:  # pylint: disable=invalid-name
        self.plugin_closing.emit()
        event.accept()
