import logging

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
)

# noinspection PyUnresolvedReferences
from qgis.utils import iface

from mi_companion.configuration import read_bool_setting
from mi_companion.qgis_utilities import (
    ANCHOR_GEOMETRY_GENERATOR_EXPRESSION,
    ROT_AND_SCALE_GEOMETRY_LINE_GENERATOR_EXPRESSION,
)

logger = logging.getLogger(__name__)


def make_rot_and_sca_symbology_layer():
    rot_and_sca_symbol_layer = QgsGeometryGeneratorSymbolLayer.create({})
    rot_and_sca_symbol_layer.setGeometryExpression(
        ROT_AND_SCALE_GEOMETRY_LINE_GENERATOR_EXPRESSION
    )
    # Create a marker sub-symbol for the points
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
    # Set the sub-symbol as a marker symbol
    rot_and_sca_symbol_layer.setSubSymbol(line_symbol)
    # Set the symbol type to point geometry
    rot_and_sca_symbol_layer.setSymbolType(Qgis.SymbolType.Line)
    return rot_and_sca_symbol_layer


def make_anchor_symbology_layer():
    anchor_symbol_layer = QgsGeometryGeneratorSymbolLayer.create({})
    anchor_symbol_layer.setGeometryExpression(ANCHOR_GEOMETRY_GENERATOR_EXPRESSION)
    # Create a marker sub-symbol for the points
    marker_symbol = QgsMarkerSymbol.createSimple({"name": "Anchor"})
    marker_symbol.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertyStrokeColor,
        QgsProperty.fromExpression('"display_rule.polygon.stroke_color"'),
    )
    marker_symbol.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertyFillColor,
        QgsProperty.fromExpression('"display_rule.polygon.stroke_color"'),
    )
    # Set the sub-symbol as a marker symbol
    anchor_symbol_layer.setSubSymbol(marker_symbol)
    # Set the symbol type to point geometry
    anchor_symbol_layer.setSymbolType(Qgis.SymbolType.Marker)
    return anchor_symbol_layer


def add_rotation_scale_geometry_generator(layers):
    """
    Add a geometry generator symbol layer with the ROT_AND_SCALE_GEOMETRY_LINE_GENERATOR_EXPRESSION to the layers.

    Args:
        layers: List of vector layers to add the geometry generator to
    """

    if not read_bool_setting("ADD_ANCHOR_AND_3DROTSCL_STYLING"):
        return

    if not layers:
        logger.error(f"{layers=} was not found")
        return

    for layer in layers:
        if not layer:
            logger.error(f"{layer=} was not found")
            continue

        # Get the renderer for this layer
        renderer = layer.renderer()
        if not renderer:
            logger.error(f"{renderer=} was not found")
            continue

        modified = False

        # Handle different renderer types
        if isinstance(renderer, QgsRuleBasedRenderer):
            # For rule-based renderers, we need to get the root rule and its children
            root_rule = renderer.rootRule()
            for child_rule in root_rule.children():
                if child_rule.symbol():
                    add_anchor_and_rot_scl_geometry_generators_to_symbol(
                        child_rule.symbol()
                    )
                    modified = True

        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            # For categorized renderers, add to each category symbol
            categories = []
            for category in renderer.categories():
                if category.symbol():
                    symbol = category.symbol().clone()
                    add_anchor_and_rot_scl_geometry_generators_to_symbol(symbol)
                    # Create a new category with the modified symbol
                    new_category = QgsRendererCategory(
                        category.value(), symbol, category.label()
                    )
                    categories.append(new_category)
                    modified = True

            # Update the renderer with new categories
            if categories:
                new_renderer = QgsCategorizedSymbolRenderer(
                    renderer.classAttribute(), categories
                )

                if renderer.sourceSymbol():
                    source_symbol = renderer.sourceSymbol().clone()
                    add_anchor_and_rot_scl_geometry_generators_to_symbol(source_symbol)
                    new_renderer.setSourceSymbol(source_symbol)

                layer.setRenderer(new_renderer)

        else:
            # For simple renderers like single symbol renderer
            symbol = renderer.symbol()
            if symbol:
                symbol = symbol.clone()
                add_anchor_and_rot_scl_geometry_generators_to_symbol(symbol)
                # Create a new renderer with the modified symbol
                new_renderer = renderer.clone()
                new_renderer.setSymbol(symbol)
                layer.setRenderer(new_renderer)

                modified = True
            else:
                logger.error(f"Symbol not found for layer {layer.name()}")

        # Trigger layer updates
        if modified:
            layer.triggerRepaint()
            layer.emitStyleChanged()
            logger.info(f"Added geometry generator to layer '{layer.name()}'")


def add_anchor_and_rot_scl_geometry_generators_to_symbol(symbol):
    """Helper function to add the geometry generator to a symbol"""

    arrow_geometry_generator = QgsGeometryGeneratorSymbolLayer.create({})
    arrow_geometry_generator.setGeometryExpression(
        ROT_AND_SCALE_GEOMETRY_LINE_GENERATOR_EXPRESSION
    )
    arrow_geometry_generator.setSymbolType(Qgis.SymbolType.Line)
    arrow_geometry_generator.setSubSymbol(
        QgsLineSymbol.createSimple(
            {
                "line_color": "255,0,0,255",
                "line_style": "solid",
                "line_width": "0.5",
                "capstyle": "round",
                "joinstyle": "round",
                "customdash": "",
                "arrow_start_width": "0",  # No arrow at start
                "arrow_start_width_unit": "MM",
                "arrow_end_width": "3",  # 3mm arrow width at end
                "arrow_end_width_unit": "MM",
                "arrow_type": "0",  # Simple arrowhead (0=regular, 1=curved)
                "head_length": "1.5",  # Length of arrowhead
                "head_length_unit": "MM",
                "head_thickness": "1.5",  # Thickness of arrowhead
                "head_thickness_unit": "MM",
                "head_type": "0",  # Fill style of arrowhead (0=filled, 1=unfilled)
            }
        )
    )

    # Create geometry generator symbol layer
    anchor_geometry_generator = QgsGeometryGeneratorSymbolLayer.create({})
    anchor_geometry_generator.setGeometryExpression(
        ANCHOR_GEOMETRY_GENERATOR_EXPRESSION
    )

    anchor_geometry_generator.setSymbolType(Qgis.SymbolType.Marker)
    anchor_geometry_generator.setSubSymbol(
        QgsMarkerSymbol.createSimple(
            {
                "name": "circle",
                "color": "0,0,255,255",  # Blue color for the anchor point
                "size": "2",  # 2mm size
                "outline_color": "0,0,0,255",  # Black outline
                "outline_width": "0.2",  # Thin outline
                "outline_style": "solid",
            }
        )
    )

    symbol.appendSymbolLayer(arrow_geometry_generator)
    symbol.appendSymbolLayer(anchor_geometry_generator)
