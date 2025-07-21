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
    QgsGeometryGeneratorSymbolLayer,
    QgsLineSymbol,
    QgsLineSymbol,
    QgsMapLayer,
    QgsMarkerSymbol,
    QgsProperty,
    QgsRendererCategory,
    QgsRuleBasedRenderer,
    QgsSymbol,
    QgsSymbol,
    QgsSymbolLayer,
    QgsWkbTypes,
    QgsWkbTypes,
)
from typing import Any

__all__ = [
    "apply_display_rule",
    "set_display_rule_conditional_formatting",
    "apply_display_rule_styling_categorized",
    "get_style_from_location_type",
    "apply_display_rule_styling_dynamic",
    "make_anchor_symbology_layer",
    "make_display_rule_styled_symbol",
    "make_rot_and_sca_symbology_layer",
    "apply_display_rule_styling_rule_based",
    "add_rotation_scale_geometry_generator",
]

from mi_companion.configuration.options import read_bool_setting
from mi_companion.qgis_utilities.expressions import (
    ANCHOR_GEOMETRY_GENERATOR_EXPRESSION,
    HEX_COLOR_POLY_FILL_EXPRESSION,
    ROT_AND_SCALE_GEOMETRY_LINE_GENERATOR_EXPRESSION,
)


logger = logging.getLogger(__name__)


def apply_display_rule(layers, display_rules) -> None: ...


def set_display_rule_conditional_formatting() -> Any: ...


def apply_display_rule_styling_categorized(layer, location_type_ref_layer):
    """
    Apply styling based on display rules from location type using a categorized renderer.

    :param layer: The layer to style
    :param location_type_ref_layer: Reference layer with location type styles
    :return: None
    """

    # Field to categorize on
    category_field = "location_type"

    # Create renderer categories list
    categories = []

    # Dictionary to store default styles for unknown location types
    default_symbol = QgsFillSymbol.createSimple(
        {
            "color": "#a0c8f0",  # Default blue fill
            "color_border": "#000000",  # Default black stroke
            "width_border": "0.5",
            "style": "solid",
            "style_border": "solid",
            "opacity": "0.7",
            "outline_width": "0.5",
            "outline_style": "solid",
        }
    )

    # Get location types and their styles from the reference layer
    if location_type_ref_layer:
        location_types = {}

        for ref_feature in location_type_ref_layer.getFeatures():
            type_id = ref_feature.attribute("admin_id")
            if type_id:
                # Create symbol for this location type
                symbol = make_display_rule_styled_symbol()

                # Add category for this location type
                category = QgsRendererCategory(type_id, symbol, str(type_id))
                categories.append(category)

    # Create a categorized renderer
    renderer = QgsCategorizedSymbolRenderer(category_field, categories)

    # Set a default symbol for features not matching any category
    renderer.setSourceSymbol(default_symbol)

    # Apply renderer to layer
    layer.setRenderer(renderer)

    # Add geometry generator layers for anchor and rotation/scale indicators
    # This approach differs from rule-based renderer by adding these to each category's symbol
    for category in renderer.categories():
        symbol = category.symbol()
        symbol.appendSymbolLayer(make_anchor_symbology_layer())
        symbol.appendSymbolLayer(make_rot_and_sca_symbology_layer())

    layer.triggerRepaint()


def apply_display_rule_styling_rule_based(layer, location_type_ref_layer):
    """
    Apply styling based on display rules from location type and individual overrides.


    :param layer:
    :param location_type_ref_layer:
    :return:
    """
    # Create a rule-based renderer
    first_level_rules = []

    # Create basic symbol with empty colors initially
    root_symbol = QgsFillSymbol.createSimple(
        {
            "style": "solid",
            "style_border": "solid",
            "outline_style": "solid",
            "outline_width_unit": "Pixel",
        }
    )

    root_symbol.appendSymbolLayer(
        make_anchor_symbology_layer()
    )  # insertSymbolLayer (0,layer)
    root_symbol.appendSymbolLayer(
        make_rot_and_sca_symbology_layer()
    )  # insertSymbolLayer (0,layer)

    # Create basic symbol with empty colors initially
    special_symbol = make_display_rule_styled_symbol()

    # Create rule with this symbol
    has_fill_color_rule = QgsRuleBasedRenderer.Rule(
        root_symbol,
        filterExp='"display_rule.polygon.fill_color" IS NOT NULL',
        label="Location Has Fill Color",
    )

    has_fill_opacity_rule = QgsRuleBasedRenderer.Rule(
        root_symbol,
        filterExp='"display_rule.polygon.fill_opacity" IS NOT NULL',
        label="Location Has Fill Opacity",
    )
    has_stroke_width_rule = QgsRuleBasedRenderer.Rule(
        root_symbol,
        filterExp='"display_rule.polygon.stroke_width" IS NOT NULL',
        label="Location Has Fill Opacity",
    )
    has_fill_stroke_color = QgsRuleBasedRenderer.Rule(
        special_symbol,
        filterExp='"display_rule.polygon.stroke_color" IS NOT NULL',
        label="Location Has Fill Opacity",
    )

    has_stroke_width_rule.appendChild(has_fill_stroke_color)
    has_fill_opacity_rule.appendChild(has_stroke_width_rule)
    has_fill_color_rule.appendChild(has_fill_opacity_rule)
    first_level_rules.append(has_fill_color_rule)

    # Second rule: Use location type style as fallback
    fallback_style_rule = QgsRuleBasedRenderer.Rule(
        QgsFillSymbol.createSimple(
            {
                "color": "@location_type_fill_color",
                "color_border": "@location_type_stroke_color",
                "width_border": "0.5",
                "style": "solid",
                "style_border": "solid",
                "opacity": "0.7",
                "outline_width": "0.5",
                "outline_style": "solid",
            }
        ),
        filterExp="ELSE",
        label="Fallback Style",
    )
    first_level_rules.append(fallback_style_rule)

    # Create the renderer and apply it
    root_rule = QgsRuleBasedRenderer.Rule(None)
    for rule in first_level_rules:
        root_rule.appendChild(rule)

    renderer = QgsRuleBasedRenderer(root_rule)

    # Add variable lookup for location type styles
    variables = QgsExpressionContextUtils.layerScope(layer)
    variables.setVariable("location_type_fill_color", "#a0c8f0")  # Default blue fill
    variables.setVariable(
        "location_type_stroke_color", "#000000"
    )  # Default black stroke

    # Get style properties from location type for this layer
    if location_type_ref_layer:
        # Create a dictionary to store location type styles
        type_styles = {}

        # Get field names to check field existence
        field_names = [field.name() for field in location_type_ref_layer.fields()]

        # Populate the dictionary with location type styles from reference layer
        for ref_feature in location_type_ref_layer.getFeatures():
            type_id = ref_feature.attribute("admin_id")
            if type_id:
                fill_color = "#a0c8f0"  # Default
                stroke_color = "#000000"  # Default

                # Try different field name possibilities
                for fill_field in [
                    "display_rule.polygon.fill_color",
                ]:
                    if fill_field in field_names:
                        fill_value = ref_feature.attribute(fill_field)
                        if fill_value:
                            fill_color = fill_value
                            break

                for stroke_field in [
                    "display_rule.polygon.stroke_color",
                ]:
                    if stroke_field in field_names:
                        stroke_value = ref_feature.attribute(stroke_field)
                        if stroke_value:
                            stroke_color = stroke_value
                            break

                type_styles[type_id] = {
                    "fill_color": fill_color,
                    "stroke_color": stroke_color,
                }

        # Create a data-defined property for fill and stroke colors
        for feature in layer.getFeatures():
            location_type = feature.attribute("location_type")
            if location_type and location_type in type_styles:
                variables.setVariable(
                    "location_type_fill_color", type_styles[location_type]["fill_color"]
                )
                variables.setVariable(
                    "location_type_stroke_color",
                    type_styles[location_type]["stroke_color"],
                )

    layer.setRenderer(renderer)
    layer.triggerRepaint()


def make_display_rule_styled_symbol():
    special_symbol = QgsFillSymbol.createSimple(
        {
            "style": "solid",
            "style_border": "solid",
            "outline_style": "solid",
            "outline_width_unit": "Pixel",
        }
    )
    # Get the symbol layer
    symbol_layer = special_symbol.symbolLayer(0)
    # Set data-defined properties for colors
    symbol_layer.setDataDefinedProperty(
        QgsSymbolLayer.PropertyFillColor, HEX_COLOR_POLY_FILL_EXPRESSION
    )
    symbol_layer.setDataDefinedProperty(
        QgsSymbolLayer.PropertyStrokeColor,
        QgsProperty.fromExpression('"display_rule.polygon.stroke_color"'),
    )
    symbol_layer.setDataDefinedProperty(
        QgsSymbolLayer.PropertyStrokeWidth,
        QgsProperty.fromExpression('"display_rule.polygon.stroke_width"'),
    )
    return special_symbol


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


def apply_display_rule_styling_dynamic(layer, location_type_ref_layer):
    """Apply styling based on display rules from location type and individual overrides."""
    # Create a rule-based renderer
    rules = []

    # First rule: Individual location has its own display_rule settings
    has_own_style_expression = (
        '"display_rule.polygon.fill_color" IS NOT NULL AND '
        '"display_rule.polygon.stroke_color" IS NOT NULL'
    )

    own_style_rule = QgsRuleBasedRenderer.Rule(
        QgsFillSymbol.createSimple(
            {
                "color": 'eval("display_rule.polygon.fill_color")',
                "color_border": 'eval("display_rule.polygon.stroke_color")',
                "width_border": "0.5",
                "style": "solid",
                "style_border": "solid",
                "opacity": 'coalesce("display_rule.polygon.fill_opacity", 0.7)',
                "outline_width": "0.5",
                "outline_style": "solid",
            }
        ),
        filterExp=has_own_style_expression,
        label="Individual Style",
    )
    rules.append(own_style_rule)

    # Create a custom expression for the second rule that looks up location type properties
    location_expr = (
        'CASE WHEN "location_type" IS NOT NULL THEN '
        '   (SELECT "display_rule.polygon.fill_color" FROM "'
        + location_type_ref_layer.name()
        + '" WHERE "admin_id" = "location_type" LIMIT 1) '
        "ELSE '#a0c8f0' END"
    )
    stroke_expr = (
        'CASE WHEN "location_type" IS NOT NULL THEN '
        '   (SELECT "display_rule.polygon.stroke_color" FROM "'
        + location_type_ref_layer.name()
        + '" WHERE "admin_id" = "location_type" LIMIT 1) '
        "ELSE '#000000' END"
    )

    # Second rule: Use location type style as fallback
    type_style_rule = QgsRuleBasedRenderer.Rule(
        QgsFillSymbol.createSimple(
            {
                "color": location_expr,
                "color_border": stroke_expr,
                "width_border": "0.5",
                "style": "solid",
                "style_border": "solid",
                "opacity": "0.7",
                "outline_width": "0.5",
                "outline_style": "solid",
            }
        ),
        filterExp="ELSE",
        label="Type Style",
    )
    rules.append(type_style_rule)

    # Create the renderer and apply it
    root_rule = QgsRuleBasedRenderer.Rule(None)
    for rule in rules:
        root_rule.appendChild(rule)

    renderer = QgsRuleBasedRenderer(root_rule)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def get_style_from_location_type(style_property, context, location_type_ref_layer):
    """Get style property from location type reference layer.

    :param style_property: The style property to retrieve (e.g., 'fill_color')
    :param context: Expression context
    :param location_type_ref_layer: Reference layer with location types
    :return: Style value or default
    """
    # Get current feature and its location type
    feature = context.feature()
    location_type_id = feature.attribute("location_type")

    # Find matching location type in reference layer
    if location_type_ref_layer and location_type_id:
        request = QgsFeatureRequest().setFilterExpression(
            f"admin_id = '{location_type_id}'"
        )
        for ref_feature in location_type_ref_layer.getFeatures(request):
            # Return the style property if found
            property_name = f"display_rule.{style_property}"
            if property_name in ref_feature.fields().names():
                return ref_feature[property_name]

    # Default colors if not found
    defaults = {
        "fill_color": "#a0c8f0",
        "stroke_color": "#000000",
        "fill_opacity": 0.7,
        "stroke_opacity": 1.0,
    }

    return defaults.get(style_property, "#a0c8f0")  # Default blue fill


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
