from typing import Any, Iterable, Sequence

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup, QgsFieldConstraints

__all__ = [
    "add_dropdown_widget",
    "make_field_unique",
    "HIDDEN_WIDGET",
    "make_field_not_null",
]

IGNORE_THIS_STRING = """

Line edit – a simple edit box
Classification – displays a combo box with the values used for “unique value” classification (symbology tab)
Range – allows numeric values within a given range, the widget can be either slider or spin box
Unique values
    editable – displays a line edit widget with auto-completion suggesting values already used in the
    attribute table
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

HIDDEN_WIDGET = QgsEditorWidgetSetup("Hidden", {})


def add_dropdown_widget(layer: Any, field_name: str, widget: Any) -> None:
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


def make_field_unique(layers: Sequence[Any], field_name: str = "admin_id") -> None:
    unique_widget = QgsEditorWidgetSetup(
        "UuidGenerator",
        {},
    )

    for layers_inner in layers:
        if layers_inner:
            if isinstance(layers_inner, Iterable):
                for layers in layers_inner:
                    if layers:
                        idx = layers.fields().indexFromName(field_name)
                        layers.setEditorWidgetSetup(
                            idx,
                            unique_widget,
                        )
                        layers.setFieldConstraint(
                            idx, QgsFieldConstraints.ConstraintNotNull
                        )
                        layers.setFieldConstraint(
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


def make_field_not_null(layers: Sequence[Any], field_name: str = "name") -> None:
    for layers_inner in layers:
        if layers_inner:
            if isinstance(layers_inner, Iterable):
                for layers in layers_inner:
                    if layers:
                        idx = layers.fields().indexFromName(field_name)

                        layers.setFieldConstraint(
                            idx, QgsFieldConstraints.ConstraintNotNull
                        )
            else:
                idx = layers_inner.fields().indexFromName(field_name)

                layers_inner.setFieldConstraint(
                    idx, QgsFieldConstraints.ConstraintNotNull
                )
