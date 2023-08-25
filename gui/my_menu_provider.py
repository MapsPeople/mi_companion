from PyQt5.QtWidgets import QMenu

# noinspection PyUnresolvedReferences
from qgis.gui import QgsLayerTreeViewMenuProvider, QgsLayerTreeViewDefaultActions


class MyMenuProvider(QgsLayerTreeViewMenuProvider):
    def __init__(self, layer_tree_view, map_canvas):
        """Initializes the provider and the factory class"""
        super(MyMenuProvider, self).__init__()
        self._view = layer_tree_view
        self._canvas = map_canvas
        self._default_actions_factory = QgsLayerTreeViewDefaultActions(self._view)

    def createContextMenu(self):
        # If user didn't right-click on a layer in the tree view
        if not self._view.currentLayer():
            return None
        m = QMenu()
        self._zoom_to_layer = self._default_actions_factory.actionZoomToLayers(
            self._canvas
        )
        m.addAction(self._zoom_to_layer)
        return m
