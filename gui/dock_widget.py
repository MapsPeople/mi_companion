import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from jord.qgis_utilities import (
    reconnect_signal,
    VectorGeometryTypeEnum,
    style_layer_from_mapping,
    categorise_layer,
    plugin_status,
)
from jord.qgis_utilities.helpers import signals
from warg import reload_module

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import pyqtSignal

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProject,
    QgsLayerTreeModel,
    QgsLayerTree,
    QgsGeometry,
    QgsFeature,
    QgsApplication,
)


from ..configuration.settings import read_project_setting, ensure_json_quotes
from ..configuration.project_settings import DEFAULT_PROJECT_SETTINGS
from ..constants import VERSION, DEFAULT_CRS, PROJECT_NAME
from ..utilities import resolve_path, get_icon_path

# from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget
# from PyQt5.QtCore import Qt

FORM_CLASS, _ = uic.loadUiType(resolve_path("dock_widget.ui", __file__))

signals.IS_DEBUGGING = True

VERBOSE = True
ITH_GROUP = 0
WKT_SEPERATOR = "\n"  # TODO: GET FROM SETTINGS!


class ServerStateEnum(Enum):
    started = "Started"
    stopped = "Stopped"


entry_point_grid


class QliveDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    plugin_closing = pyqtSignal()

    def __init__(self, iface: Any, parent: Any = None):
        """Constructor."""
        super().__init__(parent)
        self.iface = iface
        self.qgis_project = QgsProject.instance()

        if VERBOSE:
            reload_module("jord")
            reload_module("warg")

        if False:
            self.layer = self.iface.activeLayer()
            try:
                self.layer.geometryOptions().setRemoveDuplicateNodes(True)
                self.layer.geometryOptions().setGeometryChecks(
                    [
                        "QgsIsValidCheck",
                        "QgsGeometryMissingVertexCheck",
                        "QgsGeometryGapCheck",
                        "QgsGeometryOverlapCheck",
                    ]
                )
            except:
                pass
        else:
            self.layer = None

        self.plugin_dir = Path(os.path.dirname(__file__))
        self.extent_rect = None  # (xl,yl,xu,yu)
        self.is_locked = True
        self.auto_refresh = True

        self.temporary_group = None
        self.persisted_group = None
        self.selectedLayers = None

        self.edit_untoggled = False

        self.setupUi(self)

        self.mode = None
        self.qlive_layer_tree_model = None

        self.qgis_project_layer_tree_root = (
            QgsProject.instance().layerTreeRoot()
        )  # Global QGIS instance root

        self.qlive_layer_tree_root = (
            QgsLayerTree()
        )  # self.layer_tree_root.clone() # QgsLayerTree()
        if self.qlive_layer_tree_model is None:
            self.qlive_layer_tree_model = QgsLayerTreeModel(self.qlive_layer_tree_root)
            self.qlive_layer_tree_model.setFlag(QgsLayerTreeModel.AllowNodeReorder)
            self.qlive_layer_tree_model.setFlag(
                QgsLayerTreeModel.AllowNodeChangeVisibility
            )

        self.reload_qlive_root_group()

        reconnect_signal(self.classify_button.clicked, self.on_classify)
        reconnect_signal(self.server_button.clicked, self.on_server)
        reconnect_signal(self.clear_temporary_button.clicked, self.on_clear_temporary)
        reconnect_signal(self.clear_persisted_button.clicked, self.on_clear_persisted)
        reconnect_signal(self.clear_all_button.clicked, self.on_clear_all)
        reconnect_signal(self.migrate_button.clicked, self.on_migrate)
        reconnect_signal(self.zoom_button.clicked, self.on_zoom)
        reconnect_signal(self.wkt_button.clicked, self.on_wkt)

        self.server_state = ServerStateEnum.stopped

        if read_project_setting(
            "AUTO_START_SERVER",
            defaults=DEFAULT_PROJECT_SETTINGS,
            project_name=PROJECT_NAME,
        ):  # TODO: maybe move auto start to load of plugin instead in plugin.py.
            self.on_server()

        # reconnect_signal(self.iface.mapCanvas().selectionChanged, self.canvas_selection_changed)
        reconnect_signal(
            self.iface.layerTreeView().currentLayerChanged, self.layer_selection_changed
        )

        self.icon_label.setPixmap(QtGui.QPixmap(get_icon_path("qlive.png")))
        self.sponsor_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))
        self.version_label.setText(VERSION)
        self.plugin_status_label.setText(plugin_status("qlive"))

    def reload_qlive_root_group(self) -> None:
        if self.temporary_group is None:
            self.temporary_group = self.qlive_layer_tree_root.addGroup("Temporary")
        if self.persisted_group is None:
            self.persisted_group = self.qlive_layer_tree_root.addGroup("Persisted")

        self.selectedLayers = []

        self.qlive_tree_view.setModel(self.qlive_layer_tree_model)
        # self.qlive_tree_view.setMenuProvider(MyMenuProvider(self.qlive_tree_view, self.iface.mapCanvas())) # QTreeView
        # does not have this method, type must be QgsLayerTreeView instead

    def load_persisted_group(self) -> None:
        crs = DEFAULT_CRS
        uri = f"{VectorGeometryTypeEnum.point.value}"
        field = None
        if crs:
            uri += f"?crs={crs}"
        if field:
            uri += f"&field={field}"

        sd = [QgsVectorLayer(uri, "persisted_points", "memory")]

        for ith_layer, layer in enumerate(sd):
            tree_layer = self.persisted_group.insertLayer(ith_layer, layer)
            # self.persisted_group.readChildrenFromXml
            QgsProject.instance().addMapLayer(tree_layer.layer(), False)

    def on_clear_temporary(self) -> None:
        self.temporary_group.removeAllChildren()
        if False:
            if hasattr(self.iface, "mapCanvas"):
                # vLayer = self.iface.activeLayer()
                canvas = self.iface.mapCanvas()
                # canvas.waitWhileRendering()  # modification here
                extent = self.scratch_layer.extent()
                canvas.setExtent(extent)
                canvas.refresh()

    def on_clear_all(self) -> None:
        self.qlive_layer_tree_model.rootGroup().removeAllChildren()

    def on_clear_persisted(self) -> None:
        # self.persisted_group.removeAllChildren()
        self.load_persisted_group()
        buffer_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:3857&field=NAME:string(255)",
            "temporary_buffers",
            "memory",
        )
        buffer_provider = buffer_layer.dataProvider()

        buffer_features = []

        area_polygon = QgsGeometry.fromWkt(
            "POLYGON ( (6.3 -14, 52 -14, 52 -40, 6.3 -40, 6.3 -14) )"
        )

        buffer = QgsFeature()
        # buffer.setAttributes([feature['NAME']])
        buffer.setGeometry(area_polygon)
        buffer_features.append(buffer)

        buffer_provider.addFeatures(buffer_features)

        tree_layer = self.persisted_group.insertLayer(0, buffer_layer)
        # self.persisted_group.readChildrenFromXml
        QgsProject.instance().addMapLayer(tree_layer.layer(), False)

    def on_migrate(self) -> None:
        for ith_layer, tree_layer in enumerate(self.persisted_group.children()):
            self.qgis_project_layer_tree_root.insertLayer(ith_layer, tree_layer.layer())

        self.persisted_group.removeAllChildren()

    def on_moved_to_persisted(self) -> None:
        ...
        #
        # self.temporary_group.dump() # text repr of group

    def on_zoom(self) -> None:  # TODO: DOES NOT WORK!??!?
        layer = self.iface.layerTreeView().currentLayer()
        # layer = self.iface.activeLayer()
        # canvas = self.iface.activeLayer().mapCanvas()
        canvas = self.iface.mapCanvas()

        if True:
            canvas.zoomToSelected(layer)
        elif False:
            canvas.zoomToSelected()
        else:
            feats = {f.id(): f.geometry().boundingBox() for f in layer.getFeatures()}
            canvas.setExtent(feats[-1])

        canvas.refresh()

    def on_wkt(self) -> None:
        wkts = []

        layer = self.iface.layerTreeView().currentLayer()
        # layer = self.iface.activeLayer()
        if layer:
            if self.layer_check_box.isChecked():
                features = layer.getFeatures()
            else:
                features = layer.selectedFeatures()

            wkts = [feat.geometry().asWkt() for feat in features]

        if wkts:
            wkt_joined = WKT_SEPERATOR.join(wkts)

            cb = QgsApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(wkt_joined, mode=cb.Clipboard)
        else:
            print("No wkts founds")

    def on_classify(self) -> None:
        layer = self.iface.activeLayer()
        if layer:
            # layer_name = str(self.field_name_line_edit.text())
            layer_name = str(self.field_name_combo_box.currentText())

            warn_on_non_exist_field = False
            limit_categories = 10000

            if limit_categories:
                if (
                    len(layer.uniqueValues(layer.fields().indexFromName(layer_name)))
                    > limit_categories
                ):
                    return

            if self.use_mapping_check_box.isChecked():
                mapping = json.loads(
                    ensure_json_quotes(
                        read_project_setting(
                            "DEFAULT_CLASSIFY_MAPPING",
                            defaults=DEFAULT_PROJECT_SETTINGS,
                            project_name=PROJECT_NAME,
                        )
                    )
                )
                if layer_name not in mapping:
                    if warn_on_non_exist_field:
                        print(f"No mapping found for {layer_name} in {mapping}")
                        return
                else:
                    style_layer_from_mapping(
                        layer,
                        mapping,
                        layer_name,
                    )
            else:
                categorise_layer(layer, field_name=layer_name)

        else:
            print("No layer selected")

    def on_drag_and_drop(self) -> None:
        # Disallow dragging and dropping to anything other than existing groups
        ...

    def on_select(self) -> None:
        ...
        # self.selectedLayers=

    def canvas_selection_changed(self, selected_features) -> None:
        ...

    def layer_selection_changed(self, selected_layers) -> None:
        if selected_layers:
            if isinstance(selected_layers, Iterable):
                self.selectedLayers = selected_layers
            else:
                self.selectedLayers = [selected_layers]

        if len(self.selectedLayers):
            self.migrate_button.setEnabled(True)
            self.zoom_button.setEnabled(True)
            self.wkt_button.setEnabled(True)

            populate_field_names = True
            if len(self.selectedLayers) == 1 and populate_field_names:
                layer = self.selectedLayers[0]
                if (
                    not isinstance(layer, QgsRasterLayer)
                    and isinstance(layer, QgsVectorLayer)
                    and hasattr(layer, "fields")
                ):
                    field_names = self.selectedLayers[0].fields().names()
                    self.field_name_combo_box.clear()
                    self.field_name_combo_box.addItems([*field_names])
                    # self.field_name_combo_box.setCurrentIndex(0) # Auto select first field, TODO: Track last selection

        else:
            self.migrate_button.setEnabled(False)
            self.zoom_button.setEnabled(False)
            self.wkt_button.setEnabled(False)

    def on_server(self) -> None:
        # self.server.start
        if self.server_state == ServerStateEnum.stopped:
            self.server_state = ServerStateEnum.started
            self.server_button.setText("Stop Server")
            server.KEEP_RUNNING = True
            server.start_server(
                self,
                int(
                    read_project_setting(
                        "SERVER_PORT",
                        defaults=DEFAULT_PROJECT_SETTINGS,
                        project_name=PROJECT_NAME,
                    )
                ),
                int(
                    read_project_setting(
                        "SERVER_PORT_INCREMENTS",
                        defaults=DEFAULT_PROJECT_SETTINGS,
                        project_name=PROJECT_NAME,
                    )
                ),
            )
            self.server_address_label.setText(str(server.RUNNING_PORT))
        else:
            self.server_state = ServerStateEnum.stopped
            self.server_address_label.setText("No Port")
            self.server_button.setText("Start Server")
            server.KEEP_RUNNING = False

        self.status_label.setText(self.server_state.value)
        # self.reload_qlive_root_group()

    def add_layers(self) -> None:
        global ITH_GROUP
        self.temporary_group.addGroup(f"Temporary{ITH_GROUP}")
        ITH_GROUP += 1

    def on_apply(self) -> None:
        print("APPLY")
        self.layer.commitChanges(True)

    # noinspection PyPep8Naming
    def closeEvent(self, event) -> None:  # pylint: disable=invalid-name
        if VERBOSE:
            print("CLOSEEV")
        if self.layer is not None:
            self._disconnect_signals()
            # self.layer.layerModified.disconnect(self.on_modified)

        server.KEEP_RUNNING = False

        self.plugin_closing.emit()
        event.accept()
