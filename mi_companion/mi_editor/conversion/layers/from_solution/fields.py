from typing import Any, Iterable

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup, QgsFieldConstraints

__all__ = ["add_dropdown_widget", "make_field_unique", "HIDDEN_WIDGET"]


IGNORE_THIS_STRING = """

Line edit – a simple edit box
Classification – displays a combo box with the values used for “unique value” classification (symbology tab)
Range – allows numeric values within a given range, the widget can be either slider or spin box
Unique values
    editable – displays a line edit widget with auto-completion suggesting values already used in the attribute table
    not editable – displays a combo box with already used values
File name – adds a file chooser dialog
Value map – shows a combo box with predefined description/value items
Enumeration – a combo box with values that can be used within the columns type
Immutable – read-only
Hidden – makes the attribute invisible for the user
Checkbox – a checkbox with customizable representation for both checked and unchecked state
Text edit – an edit box that allow multiple input lines
Calendar – a calendar widget to input dates
"""


def add_dropdown_widget(layer, field_name: str, widget) -> None:
    # https://gis.stackexchange.com/questions/470963/setting-dropdown-on-feature-attribute-form-using-plugin
    for layers_inner in layer:
        if layers_inner:
            if isinstance(layers_inner, Iterable):
                for layer in layers_inner:
                    if layer:
                        layer.setEditorWidgetSetup(
                            layer.fields().indexFromName(field_name),
                            widget,
                        )
            else:
                layers_inner.setEditorWidgetSetup(
                    layers_inner.fields().indexFromName(field_name),
                    widget,
                )


HIDDEN_WIDGET = QgsEditorWidgetSetup("Hidden", {})


def make_field_unique(layer: Any, field_name: str = "admin_id") -> None:
    unique_widget = QgsEditorWidgetSetup(
        "UuidGenerator",
        {},
    )

    for layers_inner in layer:
        if layers_inner:
            if isinstance(layers_inner, Iterable):
                for layer in layers_inner:
                    if layer:
                        idx = layer.fields().indexFromName(field_name)
                        layer.setEditorWidgetSetup(
                            idx,
                            unique_widget,
                        )
                        layer.setFieldConstraint(
                            idx, QgsFieldConstraints.ConstraintNotNull
                        )
                        layer.setFieldConstraint(
                            idx, QgsFieldConstraints.ConstraintUnique
                        )
            else:
                idx = layers_inner.fields().indexFromName(field_name)
                layers_inner.setEditorWidgetSetup(
                    idx,
                    unique_widget,
                )
                layers_inner.setFieldConstraint(
                    idx, QgsFieldConstraints.ConstraintNotNull
                )
                layers_inner.setFieldConstraint(
                    idx, QgsFieldConstraints.ConstraintUnique
                )
