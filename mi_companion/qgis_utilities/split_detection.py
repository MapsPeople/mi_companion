def example_that_does_not_work():

    # Imports with proper QGIS modules
    from qgis.core import QgsProject, QgsVectorLayer
    from qgis.utils import iface
    from qgis.gui import QgsMapToolAdvancedDigitizing

    # Function to update anchor points after split
    def update_anchor_after_split(layer, features):
        # Check if we're currently in an edit session
        if not layer.isEditable():
            return

        # Update the anchor_x and anchor_y fields if they exist
        anchor_x_idx = layer.fields().indexFromName("anchor_x")
        anchor_y_idx = layer.fields().indexFromName("anchor_y")

        if anchor_x_idx >= 0 and anchor_y_idx >= 0:
            for fid in features:
                feature = layer.getFeature(fid)
                # Get the feature geometry
                geom = feature.geometry()
                # Calculate new anchor points using point_on_surface
                point_on_surf = geom.pointOnSurface().asPoint()
                anchor_x = point_on_surf.x()
                anchor_y = point_on_surf.y()
                layer.changeAttributeValue(fid, anchor_x_idx, anchor_x)
                layer.changeAttributeValue(fid, anchor_y_idx, anchor_y)

    # Track the active edit tool to detect split operations
    previous_tool = None

    def tool_changed(tool):
        global previous_tool
        current_tool = iface.mapCanvas().mapTool()

        # Check if we're coming from a split tool (detecting after split operation)
        if (
            previous_tool
            and "Split" in previous_tool.__class__.__name__
            and current_tool != previous_tool
        ):
            layer = iface.activeLayer()
            if isinstance(layer, QgsVectorLayer) and layer.isEditable():
                # Get newly added features (result of split)
                added_features = (
                    layer.editBuffer().addedFeatures().keys()
                    if layer.editBuffer()
                    else []
                )
                if added_features:
                    update_anchor_after_split(layer, added_features)

        previous_tool = current_tool

    # Connect to the map tool changed signal
    iface.mapCanvas().mapToolSet.connect(tool_changed)

    # Connect to the editingStarted signal to monitor layers entering edit mode
    def setup_split_monitoring(layer):
        if isinstance(layer, QgsVectorLayer):
            layer.editCommandEnded.connect(lambda: check_for_splits(layer))

    def check_for_splits(layer):
        # Check if the last edit operation was a split
        edit_command = layer.undoStack().command(layer.undoStack().index() - 1)
        if edit_command and "Split" in edit_command.text():
            # Get newly added features
            added_features = (
                layer.editBuffer().addedFeatures().keys() if layer.editBuffer() else []
            )
            if added_features:
                update_anchor_after_split(layer, added_features)

    # Connect to all existing layers
    for layer in QgsProject.instance().mapLayers().values():
        if isinstance(layer, QgsVectorLayer):
            layer.editingStarted.connect(lambda l=layer: setup_split_monitoring(l))

    # Connect to layersAdded signal for new layers (corrected from layerAdded)
    QgsProject.instance().layersAdded.connect(
        lambda layers: [
            layer.editingStarted.connect(lambda l=layer: setup_split_monitoring(l))
            for layer in layers
            if isinstance(layer, QgsVectorLayer)
        ]
    )
