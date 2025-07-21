# noinspection PyUnresolvedReferences
from typing import Any

from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsExpression,
    QgsRendererCategory,
    QgsRendererRange,
    QgsStyle,
    QgsSymbol,
)


def set_m_based_categorised_styling_single_layer(
    layer: Any, *, repaint: bool = False
) -> None:
    """
    Sets a graduated color style based on unique z-coordinates.
    Each unique m value gets assigned a different color.
    """

    unique_vals = set()

    sample_point = 0.5

    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom:
            m_val = geom.constGet().mAt(sample_point)  # Get z from first vertex
            unique_vals.add(m_val)

    # unique_vals.sort()
    unique_vals = sorted(unique_vals)

    ramp = QgsStyle.defaultStyle().colorRamp("Spectral")

    render_categories = []
    for i, m_val in enumerate(unique_vals):
        color = ramp.color(i / (len(unique_vals) - 1 if len(unique_vals) > 1 else 1))

        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(color)

        render_categories.append(
            QgsRendererCategory(
                m_val, symbol=symbol, label=f"Level {m_val}", render=True
            )
        )

    renderer = QgsCategorizedSymbolRenderer(
        f"m_at($geometry,{sample_point})", render_categories
    )
    layer.setRenderer(renderer)
    if repaint:
        layer.triggerRepaint()
