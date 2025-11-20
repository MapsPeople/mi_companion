import logging
import re

# noinspection PyUnresolvedReferences
from qgis.core import (
    Qgis,
    QgsCategorizedSymbolRenderer,
    QgsDefaultValue,
    QgsEditorWidgetSetup,
    QgsExpression,
    QgsExpressionContextUtils,
    QgsExpressionFunction,
    QgsFeatureRequest,
    QgsFieldConstraints,
    QgsFillSymbol,
    QgsGeometryGeneratorSymbolLayer,
    QgsLineSymbol,
    QgsMapLayer,
    QgsMarkerSymbol,
    QgsProperty,
    QgsRasterMarkerSymbolLayer,
    QgsRendererCategory,
    QgsRuleBasedRenderer,
    QgsSingleSymbolRenderer,
    QgsSvgMarkerSymbolLayer,
    QgsSymbol,
    QgsSymbolLayer,
    QgsWkbTypes,
    QgsSimpleMarkerSymbolLayer,
    QgsMarkerSymbolLayer,
    QgsApplication,
    QgsProject,
    QgsUnitTypes,
    QgsGraduatedSymbolRenderer,
    QgsRendererRange,

)
import os
from PyQt5.QtGui import QColor
# noinspection PyUnresolvedReferences
from qgis.utils import iface

from mi_companion.configuration import read_bool_setting
from mi_companion.qgis_utilities import (
    ANCHOR_GEOMETRY_GENERATOR_EXPRESSION,
    ROT_AND_SCALE_GEOMETRY_LINE_GENERATOR_EXPRESSION,
)

logger = logging.getLogger(__name__)


__all__ = [
    "make_rot_and_sca_symbology_layer",
    "make_anchor_symbology_layer",
    "add_rotation_scale_geometry_generator",
    "remove_rotation_scale_geometry_generator"
]


def make_rot_and_sca_symbology_layer():
    """
    Create a geometry generator symbol layer for rotation and scale visualization.

    :return: QgsGeometryGeneratorSymbolLayer configured for rotation/scale display
    """
    rot_and_sca_symbol_layer = QgsGeometryGeneratorSymbolLayer.create({})
    rot_and_sca_symbol_layer.setGeometryExpression(
        ROT_AND_SCALE_GEOMETRY_LINE_GENERATOR_EXPRESSION
    )

    line_symbol = QgsLineSymbol.createSimple(
        {
            "name": "Rotation and Scale",
        }
    )
    line_symbol.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertyStrokeColor,
        QgsProperty.fromExpression('"display_rule.polygon.stroke_color"'),
    )
    line_symbol.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertyFillColor,
        QgsProperty.fromExpression('"display_rule.polygon.stroke_color"'),
    )

    rot_and_sca_symbol_layer.setSubSymbol(line_symbol)
    rot_and_sca_symbol_layer.setSymbolType(Qgis.SymbolType.Line)

    return rot_and_sca_symbol_layer


def make_anchor_symbology_layer():
    """
    Create a geometry generator symbol layer for anchor point visualization.

    :return: QgsGeometryGeneratorSymbolLayer configured for anchor display
    """
    anchor_symbol_layer = QgsGeometryGeneratorSymbolLayer.create({})
    anchor_symbol_layer.setGeometryExpression(ANCHOR_GEOMETRY_GENERATOR_EXPRESSION)

    marker_symbol = QgsMarkerSymbol.createSimple({"name": "Anchor"})
    marker_symbol.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertyStrokeColor,
        QgsProperty.fromExpression('"display_rule.polygon.stroke_color"'),
    )
    marker_symbol.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertyFillColor,
        QgsProperty.fromExpression('"display_rule.polygon.stroke_color"'),
    )

    anchor_symbol_layer.setSubSymbol(marker_symbol)
    anchor_symbol_layer.setSymbolType(Qgis.SymbolType.Marker)

    return anchor_symbol_layer

def _rule_matches_location_types(rule, location_types_with_3d):
    """
    Returns True if the rule has filter expression includes any of the location_types_with_3d.
    """
    if not rule.filterExpression():
        return True  # no filter = apply to all
    for lt in location_types_with_3d:
        if f'"location_type" = \'{lt}\'' in rule.filterExpression():
            return True
    return False

def add_rotation_scale_geometry_generator(layers, location_types_with_3d=None):
    """
    Add 3D rotation/anchor geometry generators (red arrow + blue dot) to features in layers.
    Only features matching location_types_with_3d will get the indicators.

    Args:
        layers: List of QgsVectorLayer
        location_types_with_3d: Optional set of location_type values to filter features
    """
    if not layers:
        logger.info("No layers provided.")
        return

    for layer in layers:
        if not layer:
            continue
        renderer = layer.renderer()
        if not renderer:
            continue

        modified = False
        logger.info(f"Processing layer '{layer.name()}' ({type(renderer).__name__})")

        # Rule-based Renderer
        if isinstance(renderer, QgsRuleBasedRenderer):
            root_rule = renderer.rootRule()
            for rule in root_rule.children():
                symbol = rule.symbol()
                if symbol:
                    # Apply only if rule filter matches location_types_with_3d or if no filter
                    if (not location_types_with_3d) or _rule_matches_location_types(rule, location_types_with_3d):
                        symbol = symbol.clone()
                        add_anchor_and_rot_scl_geometry_generators_to_symbol(symbol)
                        rule.setSymbol(symbol)
                        modified = True

        # Categorized Renderer
        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            new_categories = []
            for cat in renderer.categories():
                symbol = cat.symbol().clone()
                # Only add indicators if category value is in the filter
                if not location_types_with_3d or cat.value() in location_types_with_3d:
                    add_anchor_and_rot_scl_geometry_generators_to_symbol(symbol)
                    modified = True
                new_categories.append(QgsRendererCategory(cat.value(), symbol, cat.label()))

            new_renderer = QgsCategorizedSymbolRenderer(renderer.classAttribute(), new_categories)
            if renderer.sourceSymbol():
                new_renderer.setSourceSymbol(renderer.sourceSymbol().clone())
            layer.setRenderer(new_renderer)

        # Graduated Renderer
        elif isinstance(renderer, QgsGraduatedSymbolRenderer):
            new_ranges = []
            for r in renderer.ranges():
                symbol = r.symbol().clone()
                # Check if the range label/value is in the filter (optional)
                if not location_types_with_3d or str(r.label()) in location_types_with_3d or str(r.lowerValue()) in location_types_with_3d:
                    add_anchor_and_rot_scl_geometry_generators_to_symbol(symbol)
                    modified = True
                new_range = QgsRendererRange(r.lowerValue(), r.upperValue(), symbol, r.label())
                new_ranges.append(new_range)

            new_renderer = QgsGraduatedSymbolRenderer(renderer.classAttribute(), new_ranges)
            new_renderer.setMode(renderer.mode())
            if renderer.sourceSymbol():
                new_renderer.setSourceSymbol(renderer.sourceSymbol().clone())
            layer.setRenderer(new_renderer)

        # Single-symbol renderer
        elif hasattr(renderer, "symbol") and callable(renderer.symbol):
            symbol = renderer.symbol()
            if symbol:
                symbol = symbol.clone()
                # Apply filter: check feature attribute via expression
                if not location_types_with_3d:
                    add_anchor_and_rot_scl_geometry_generators_to_symbol(symbol)
                    modified = True
                # Otherwise, for single symbol you would need to convert to rule-based to apply filter

                new_renderer = renderer.clone()
                new_renderer.setSymbol(symbol)
                layer.setRenderer(new_renderer)

        # Update layer
        if modified:
            layer.triggerRepaint()
            layer.emitStyleChanged()
            logger.info(f"✓ Added 3D indicators to layer '{layer.name()}'")

def add_anchor_and_rot_scl_geometry_generators_to_symbol(symbol):
    """
    Adds 3D rotation/anchor geometry generators (red arrow + blue dot) to a symbol.
    Both markers are responsive to map zoom using @map_scale.
    """

    # Red Arrow Geometry Generator
    direction_geometry_generator = QgsGeometryGeneratorSymbolLayer.create({})
    direction_geometry_generator.setGeometryExpression('make_point("anchor_x", "anchor_y")')
    direction_geometry_generator.setSymbolType(Qgis.SymbolType.Marker)

    # Load SVG arrow
    svg_filename = 'arrows/arrow_06.svg'
    svg_path = None
    for base_path in QgsApplication.svgPaths():
        candidate = os.path.join(base_path, svg_filename)
        if os.path.exists(candidate):
            svg_path = candidate
            break

    if not svg_path:
        project_dir = QgsProject.instance().homePath()
        local_candidate = os.path.join(project_dir, svg_filename)
        if os.path.exists(local_candidate):
            svg_path = local_candidate
        else:
            raise FileNotFoundError(f"Cannot find {svg_filename} in QGIS paths or project directory")

    # Create SVG marker
    marker_symbol = QgsMarkerSymbol()
    svg_marker = QgsSvgMarkerSymbolLayer(svg_path)
    # Set width to 10 and height to 20

    svg_marker.setSize(10)  # This sets the width

    svg_marker.setColor(QColor(255, 0, 0))

    # Set anchor point to bottom of the arrow
    svg_marker.setVerticalAnchorPoint(QgsMarkerSymbolLayer.VerticalAnchorPoint.Bottom)

    # Replace the default marker with our SVG marker
    marker_symbol.changeSymbolLayer(0, svg_marker)

    # Apply rotation to the marker to match the rotation_z value
    marker_symbol.setDataDefinedAngle(
        QgsProperty.fromExpression('"display_rule.model3d.rotation_z"')
    )

    direction_geometry_generator.setSubSymbol(marker_symbol)

    # The anchor point marker (blue dot) if still needed
    anchor_geometry_generator = QgsGeometryGeneratorSymbolLayer.create({})
    anchor_geometry_generator.setGeometryExpression('make_point("anchor_x", "anchor_y")')
    anchor_geometry_generator.setSymbolType(Qgis.SymbolType.Marker)

    anchor_symbol = QgsMarkerSymbol.createSimple({
        'name': 'circle',
        'size': '2',
        'color': '0,0,255,255'
    })

    anchor_geometry_generator.setSubSymbol(anchor_symbol)

    # Add both geometry generators to the symbol
    symbol.appendSymbolLayer(direction_geometry_generator)
    symbol.appendSymbolLayer(anchor_geometry_generator)

def remove_rotation_scale_geometry_generator(layers, location_types_with_3d=None):
    """
    Remove 3D rotation/anchor geometry generators only from features matching
    location_types_with_3d in the given layers.
    
    Args:
        layers: List of QgsVectorLayer
        location_types_with_3d: Optional set of location_type values to filter which features to remove
    """
    if not layers:
        return

    for layer in layers:
        renderer = layer.renderer()
        if not renderer:
            continue

        modified = False

        # Rule-based
        if isinstance(renderer, QgsRuleBasedRenderer):
            for rule in renderer.rootRule().children():
                symbol = rule.symbol()
                if symbol:
                    if not location_types_with_3d or _rule_matches_location_types(rule, location_types_with_3d):
                        if remove_anchor_and_rot_scl_geometry_generators_from_symbol(symbol):
                            modified = True

        # Categorized
        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            new_categories = []
            for cat in renderer.categories():
                symbol = cat.symbol().clone()
                if not location_types_with_3d or cat.value() in location_types_with_3d:
                    if remove_anchor_and_rot_scl_geometry_generators_from_symbol(symbol):
                        modified = True
                new_categories.append(QgsRendererCategory(cat.value(), symbol, cat.label()))
            new_renderer = QgsCategorizedSymbolRenderer(renderer.classAttribute(), new_categories)
            if renderer.sourceSymbol():
                new_renderer.setSourceSymbol(renderer.sourceSymbol().clone())
            layer.setRenderer(new_renderer)

        # Graduated
        elif isinstance(renderer, QgsGraduatedSymbolRenderer):
            new_ranges = []
            for r in renderer.ranges():
                symbol = r.symbol().clone()
                if not location_types_with_3d or str(r.label()) in location_types_with_3d or str(r.lowerValue()) in location_types_with_3d:
                    if remove_anchor_and_rot_scl_geometry_generators_from_symbol(symbol):
                        modified = True
                new_range = QgsRendererRange(r.lowerValue(), r.upperValue(), symbol, r.label())
                new_ranges.append(new_range)
            new_renderer = QgsGraduatedSymbolRenderer(renderer.classAttribute(), new_ranges)
            new_renderer.setMode(renderer.mode())
            if renderer.sourceSymbol():
                new_renderer.setSourceSymbol(renderer.sourceSymbol().clone())
            layer.setRenderer(new_renderer)

        # Single-symbol
        elif hasattr(renderer, "symbol") and callable(renderer.symbol):
            symbol = renderer.symbol().clone()
            # Cannot filter per feature here unless we convert to rule-based, so we remove only if no filter
            if not location_types_with_3d:
                if remove_anchor_and_rot_scl_geometry_generators_from_symbol(symbol):
                    new_renderer = renderer.clone()
                    new_renderer.setSymbol(symbol)
                    layer.setRenderer(new_renderer)
                    modified = True

        # Update layer
        if modified:
            layer.triggerRepaint()
            layer.emitStyleChanged()

def remove_anchor_and_rot_scl_geometry_generators_from_symbol(symbol):
    """
    Remove anchor and rotation/scale geometry generator symbol layers
    (red arrow + blue dot) from a given symbol.

    Returns:
        bool: True if at least one layer was removed, False otherwise.
    """
    removed_any = False
    layers_to_remove = []

    for index, symbol_layer in enumerate(symbol.symbolLayers()):
        if isinstance(symbol_layer, QgsGeometryGeneratorSymbolLayer):
            sub_symbol = symbol_layer.subSymbol()
            if not sub_symbol:
                continue

            # Check for SVG red arrow
            if any(
                isinstance(sub_symbol, QgsSvgMarkerSymbolLayer) and
                sub_symbol.color().red() == 255 and sub_symbol.color().green() == 0 and sub_symbol.color().blue() == 0
                for sub_symbol in sub_symbol.symbolLayers()
            ):
                layers_to_remove.append(index)
                continue

            # Check for blue anchor dot
            if any(
                isinstance(sub_symbol, QgsSimpleMarkerSymbolLayer) and
                sub_symbol.color().red() == 0 and sub_symbol.color().green() == 0 and sub_symbol.color().blue() == 255
                for sub_symbol in sub_symbol.symbolLayers()
            ):
                layers_to_remove.append(index)
                continue

    # Remove layers in reverse order to avoid index shifting
    for index in sorted(layers_to_remove, reverse=True):
        symbol.deleteSymbolLayer(index)
        removed_any = True

    return removed_any
