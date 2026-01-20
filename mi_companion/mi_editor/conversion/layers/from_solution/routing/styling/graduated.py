# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsExpression,
    QgsGraduatedSymbolRenderer,
    QgsRendererRange,
    QgsStyle,
    QgsSymbol,
)
from typing import Any, Collection, Iterable


def set_z_based_graduated_styling(
    layers: Collection[Any], *, repaint: bool = False
) -> None:
    """

    :param layers:
    :param repaint:
    :return:
    """
    for layers_inner in layers:
        if layers_inner:
            if isinstance(layers_inner, Iterable):
                for layer in layers_inner:
                    if layer:
                        set_z_based_graduated_styling_single_layer(
                            layer, repaint=repaint
                        )
            else:
                set_z_based_graduated_styling_single_layer(
                    layers_inner, repaint=repaint
                )


def set_m_based_graduated_styling(
    layers: Collection[Any], *, repaint: bool = False
) -> None:
    """

    :param layers:
    :param repaint:
    :return:
    """
    for layers_inner in layers:
        if layers_inner:
            if isinstance(layers_inner, Iterable):
                for layer in layers_inner:
                    if layer:
                        set_m_based_graduated_styling_single_layer(
                            layer, repaint=repaint
                        )
            else:
                set_m_based_graduated_styling_single_layer(
                    layers_inner, repaint=repaint
                )


def set_m_based_graduated_styling_single_layer(
    layer: Collection[Any], *, repaint: bool = False
) -> None:
    """
    Sets a graduated color style based on unique z-coordinates.
    Each unique z value gets assigned a different color.
    """

    # z_expression = QgsExpression("z_max($geometry)")
    # z_expression.prepare(layer.fields())
    # unique_vals = []
    unique_vals = set()

    for feature in layer.getFeatures():
        if False:
            # m_val = z_expression.evaluate(feature)
            # if m_val not in unique_vals:
            #    unique_vals.append(m_val)
            ...
        else:
            geom = feature.geometry()
            if geom:
                m_val = geom.constGet().mAt(0)  # Get z from first vertex
                unique_vals.add(m_val)

    # unique_vals.sort()
    unique_vals = sorted(unique_vals)

    ramp = QgsStyle.defaultStyle().colorRamp("Spectral")

    ranges = []
    for i, m_val in enumerate(unique_vals):
        color = ramp.color(i / (len(unique_vals) - 1 if len(unique_vals) > 1 else 1))

        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(color)

        range_label = f"Level {m_val}"
        value_range = QgsRendererRange(m_val, m_val, symbol, range_label)
        ranges.append(value_range)

    renderer = QgsGraduatedSymbolRenderer("m_max($geometry)", ranges)
    layer.setRenderer(renderer)
    if repaint:
        layer.triggerRepaint()


def set_z_based_graduated_styling_single_layer(
    layer: Collection[Any], *, repaint: bool = False
) -> None:
    """
    Sets a graduated color style based on unique z-coordinates.
    Each unique z value gets assigned a different color.
    """

    # z_expression = QgsExpression("z_max($geometry)")
    # z_expression.prepare(layer.fields())
    # unique_vals = []
    unique_vals = set()

    for feature in layer.getFeatures():
        if False:
            # z_val = z_expression.evaluate(feature)
            # if z_val not in unique_vals:
            #  unique_vals.append(z_val)
            ...
        else:
            geom = feature.geometry()
            if geom:
                z_val = geom.constGet().zAt(0)  # Get z from first vertex
                unique_vals.add(z_val)

    # unique_vals.sort()
    unique_vals = sorted(unique_vals)

    ramp = QgsStyle.defaultStyle().colorRamp("Spectral")

    ranges = []
    for i, z_val in enumerate(unique_vals):
        color = ramp.color(i / (len(unique_vals) - 1 if len(unique_vals) > 1 else 1))

        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(color)

        range_label = f"Level {z_val}"
        value_range = QgsRendererRange(z_val, z_val, symbol, range_label)
        ranges.append(value_range)

    renderer = QgsGraduatedSymbolRenderer("z_max($geometry)", ranges)
    layer.setRenderer(renderer)
    if repaint:
        layer.triggerRepaint()
