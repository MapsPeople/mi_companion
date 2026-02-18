__all__ = ["set_graph_styling"]


from typing import Any, Collection, Iterable

from qgis.PyQt.QtCore import QPointF
from qgis.core import (
    Qgis,
    QgsGraduatedSymbolRenderer,
    QgsLineSymbol,
    QgsLinearReferencingSymbolLayer,
    QgsProperty,
    QgsRendererRange,
    QgsStyle,
)
from warg import frange, pairs

dashing_style_in_highway_type_expression = """if(
	"highway" = 'footway',
	'solid',
	if(
		"highway" = 'steps',
		'dash',
		if(
			"highway" = 'elevator',
			'dot',
			'dash dot dot'
		)
	)
)
"""

mean_m = "(m_min(@geometry)+m_max(@geometry)) / 2"


def set_graph_styling(layers: Collection[Any], *, repaint: bool = False) -> None:
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
                        set_m_and_highway_styling_single_layer(layer, repaint=repaint)
            else:
                set_m_and_highway_styling_single_layer(layers_inner, repaint=repaint)


def m_symbol() -> QgsLineSymbol:
    """

    :return:
    :rtype:
    """
    line_symbol = QgsLineSymbol.createSimple({"name": "M (level) values"})
    line_symbol.setWidth(1)
    # line_symbol.setWidthUnit
    line_symbol.symbolLayer(0).setDataDefinedProperty(
        QgsLinearReferencingSymbolLayer.PropertyStrokeStyle,
        QgsProperty.fromExpression(dashing_style_in_highway_type_expression),
    )

    linear_ref_layer = QgsLinearReferencingSymbolLayer()
    linear_ref_layer.setPlacement(Qgis.LinearReferencingPlacement.Vertex)
    # linear_ref_layer.setFormat(QgsTextFormat().fromQFont(QFont("Arial", 8)))
    linear_ref_layer.setLabelOffset(QPointF(1, 1))
    # linear_ref_layer.setLabelOffsetUnit(Qgis.RenderUnit.Millimeters)
    linear_ref_layer.setLabelSource(Qgis.LinearReferencingLabelSource.M)

    a = """if(
	m_at(geometry,0) = m_at(geometry,-1),
	$length,
	abs(m_max(geometry) - m_min(geometry))
)"""

    line_symbol.appendSymbolLayer(linear_ref_layer)
    # line_symbol.insertSymbolLayer(0, linear_ref_layer)
    return line_symbol


def set_m_and_highway_styling_single_layer(
    layer: Collection[Any], *, repaint: bool = False
) -> None:
    """

    :param layer:
    :type layer:
    :param repaint:
    :type repaint:
    """
    unique_vals = set()

    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom:
            unique_vals.add(geom.constGet().mAt(0))  # Get m from first vertex

    unique_vals = sorted(unique_vals)
    if len(unique_vals) > 1:
        min_interval = min(b - a for a, b in pairs(unique_vals)) / 2
        half_min_interval = min_interval / 2
    else:
        min_interval = 1
        half_min_interval = 1

    ramp = QgsStyle.defaultStyle().colorRamp("Turbo")

    if True:
        ranges = []
        a = list(frange(min(unique_vals), max(unique_vals), min_interval))
        for i, z_val in enumerate(a):
            color = ramp.color(i / (len(a) - 1 if len(a) > 1 else 1))

            # symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol = m_symbol()
            symbol.setColor(color)

            range_label = f"Level {z_val} +-{half_min_interval:.1f}"
            value_range = QgsRendererRange(
                z_val - half_min_interval,
                z_val + half_min_interval,
                symbol,
                range_label,
            )
            ranges.append(value_range)

        max_value = 1000000000000

        # symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol = m_symbol()
        symbol.setColor(ramp.color(0))
        min_value_range = QgsRendererRange(
            -max_value, min(a) - half_min_interval, symbol, f"Outside Range Negative"
        )
        ranges.insert(0, min_value_range)

        # symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol = m_symbol()
        symbol.setColor(ramp.color(1))
        max_value_range = QgsRendererRange(
            max(a) + half_min_interval, max_value, symbol, f"Outside Range Positive"
        )
        ranges.append(max_value_range)

        renderer = QgsGraduatedSymbolRenderer(mean_m, ranges)

    layer.setRenderer(renderer)
    if repaint:
        layer.triggerRepaint()
