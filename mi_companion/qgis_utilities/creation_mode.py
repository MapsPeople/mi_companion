import logging

from mi_companion.layer_descriptors import (
    LOCATION_DESCRIPTORS,
)
from .expressions import (
    DEFAULT_NAME_GET_LOCATION_TYPE_NAME_EXPRESSION,
    NAME_MUST_NOT_NULL_AND_NOT_EMPTY_VALIDATION_EXPRESSION,
)

logger = logging.getLogger(__name__)


CREATION_MODE_FIELDS = ["location_type", "external_id", "anchor_x", "anchor_y"]


def put_location_layers_into_creation_mode():
    """
    Set all location layers into creation mode by applying constraints and default values.
    This sets field constraints for name field and provides default values based on location type.
    """
    from qgis.core import (
        QgsProject,
        QgsFieldConstraints,
        QgsDefaultValue,
        QgsEditorWidgetSetup,
    )

    # Get all layers from the project
    layers = QgsProject.instance().mapLayers().values()

    # Filter for location layers (adjust criteria as needed)
    location_layers = [
        layer
        for layer in layers
        if any(layer.name().lower().startswith(a) for a in LOCATION_DESCRIPTORS)
    ]

    for layer in location_layers:
        # Get all fields from the layer
        fields = layer.fields()

        hide_all_other_fields(layer, CREATION_MODE_FIELDS)

        # Find name fields, including translations
        for field_idx in range(fields.count()):
            field_name = fields.at(field_idx).name()

            # Check if it's a name field or a translation field
            if "translations." in field_name and field_name.endswith(".name"):

                layer.setConstraintExpression(
                    field_idx,
                    NAME_MUST_NOT_NULL_AND_NOT_EMPTY_VALIDATION_EXPRESSION.format(
                        field_name=field_name
                    ),
                    "Name cannot be empty",
                )

                if False:
                    layer.setFieldConstraint(
                        field_idx,
                        QgsFieldConstraints.ConstraintNotNull,
                        QgsFieldConstraints.ConstraintStrengthSoft,
                    )

                layer.setFieldConstraint(
                    field_idx,
                    QgsFieldConstraints.ConstraintExpression,
                    QgsFieldConstraints.ConstraintStrengthHard,
                )

                # Set default value for the name field
                default_value = QgsDefaultValue(
                    DEFAULT_NAME_GET_LOCATION_TYPE_NAME_EXPRESSION, applyOnUpdate=True
                )
                layer.setDefaultValueDefinition(field_idx, default_value)

                # Set expression check widget
                widget_setup = QgsEditorWidgetSetup(
                    "TextEdit", {"IsMultiline": False, "UseHtml": False}
                )
                layer.setEditorWidgetSetup(field_idx, widget_setup)

    # Update the layers to apply changes
    for layer in location_layers:
        layer.triggerRepaint()


def put_location_layer_into_regular_mode():
    """
    Set all location layers back into regular mode by:
    1. Removing constraints and default values that were set during creation mode
    2. Restoring all fields not in CREATION_MODE_FIELDS to TextEdit widgets
    """
    from qgis.core import (
        QgsProject,
        QgsFieldConstraints,
        QgsDefaultValue,
        QgsEditorWidgetSetup,
    )

    # Get all layers from the project
    layers = QgsProject.instance().mapLayers().values()

    # Filter for location layers
    location_layers = [
        layer
        for layer in layers
        if any(layer.name().lower().startswith(a) for a in LOCATION_DESCRIPTORS)
    ]

    for layer in location_layers:
        # Get all fields from the layer
        fields = layer.fields()

        # First handle the name fields and their constraints
        for field_idx in range(fields.count()):
            field_name = fields.at(field_idx).name()

            # Check if it's a name field or a translation field
            if "translations." in field_name and field_name.endswith(".name"):
                layer.setDefaultValueDefinition(field_idx, QgsDefaultValue(""))

        # Now restore non-CREATION_MODE_FIELDS to TextEdit
        for field_idx in range(fields.count()):
            field_name = fields.at(field_idx).name()

            if field_name not in CREATION_MODE_FIELDS:
                # Reset to standard text widget setup
                widget_setup = QgsEditorWidgetSetup(
                    "TextEdit", {"IsMultiline": False, "UseHtml": False}
                )
                layer.setEditorWidgetSetup(field_idx, widget_setup)
                logger.debug(f"Restoring field '{field_name}' to TextEdit widget")

    # Update the layers to apply changes
    for layer in location_layers:
        layer.triggerRepaint()


def hide_all_other_fields(layer, fields_to_keep_visible) -> None:
    """
    Hide all fields in the attribute form except for the specified ones.


    Args:
        layer: QgsVectorLayer to modify
        fields_to_keep_visible: String or list of field names to keep visible
    """
    from qgis.core import QgsEditorWidgetSetup

    # Convert single field to list for consistent handling
    if isinstance(fields_to_keep_visible, str):
        fields_to_keep_visible = [fields_to_keep_visible]

    logger.info(
        f"Hiding all fields except {fields_to_keep_visible} in layer '{layer.name()}'"
    )

    # Get all fields from the layer
    layer_fields = layer.fields()

    # Track if we found any fields to keep
    found_fields = set()

    # Iterate through all fields
    for field_idx in range(layer_fields.count()):
        field_name = layer_fields.at(field_idx).name()

        # If this is a field we want to keep visible
        if field_name in fields_to_keep_visible:
            # Get current widget setup to preserve original widget
            current_setup = layer.editorWidgetSetup(field_idx)
            found_fields.add(field_name)
            logger.debug(
                f"Keeping field '{field_name}' visible with widget type '{current_setup.type()}'"
            )
        else:
            # Hide field by using "Hidden" widget type
            new_setup = QgsEditorWidgetSetup("Hidden", {})
            layer.setEditorWidgetSetup(field_idx, new_setup)
            logger.debug(f"Hiding field '{field_name}' using Hidden widget")

    # Check for any fields that weren't found
    missing_fields = set(fields_to_keep_visible) - found_fields
    if missing_fields:
        logger.warning(f"Fields {missing_fields} not found in layer '{layer.name()}'")
