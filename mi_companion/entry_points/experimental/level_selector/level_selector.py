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
    QgsLayerTreeModel,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)

# noinspection PyUnresolvedReferences
from qgis.gui import QgsDockWidget
from warg import ensure_in_sys_path

from mi_companion.utilities.paths import resolve_path

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

FORM_CLASS, _ = uic.loadUiType(resolve_path("level_selector.ui", __file__))

signals.IS_DEBUGGING = True
logger = logging.getLogger(__name__)
VERBOSE = False
LOGGER = logger


ensure_in_sys_path(Path(__file__).parent.parent)

from qgis.utils import iface


class LevelSelectorWidget(QgsDockWidget, FORM_CLASS):
    plugin_closing = pyqtSignal()

    def __init__(self, iface_: Any, parent: Optional[Any] = None):
        """Constructor."""
        super().__init__(parent)

        self.selectedLayers = None
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
                self.selectedLayers = selected_layers
            else:
                self.selectedLayers = [selected_layers]

        unique_level_values = set()
        if len(self.selectedLayers):
            self.gather_unique_levels(self.selectedLayers, unique_level_values)

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
                    for v in layer.getFeatures():
                        unique_level_values.add(str(v.attributes()[col_idx]))

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
