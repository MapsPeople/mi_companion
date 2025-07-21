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

logger = logging.getLogger(__name__)
from mi_companion.qgis_utilities import ANCHOR_GEOMETRY_GENERATOR_EXPRESSION


def add_raster_with_geometry_generator(symbol):
    """
    Add a raster marker with its own geometry generator to the symbol.

    Args:
        symbol: The symbol to add the raster generator to
    """
    # Create a geometry generator symbol layer for the raster
    geo_layer = QgsGeometryGeneratorSymbolLayer.create({})
    geo_layer.setGeometryExpression(ANCHOR_GEOMETRY_GENERATOR_EXPRESSION)
    geo_layer.setSymbolType(Qgis.SymbolType.Marker)

    # Create a sub-symbol for the geometry generator
    sub_symbol = QgsMarkerSymbol.createSimple({})

    # Clear any default symbol layers in the sub-symbol
    while sub_symbol.symbolLayerCount() > 0:
        sub_symbol.deleteSymbolLayer(0)

    # Create raster layer and add it to the sub-symbol
    raster_layer = create_raster_symbol_layer()
    sub_symbol.appendSymbolLayer(raster_layer)

    # Set the sub-symbol to the geometry generator
    geo_layer.setSubSymbol(sub_symbol)

    # Add the geometry generator to the main symbol
    symbol.appendSymbolLayer(geo_layer)


def create_raster_symbol_layer():
    """Create and configure a raster marker symbol layer"""
    # Create raster layer
    raster_layer = QgsRasterMarkerSymbolLayer.create({})

    # Set data-defined properties for raster path, scale and rotation
    raster_layer.setDataDefinedProperty(
        QgsSymbolLayer.PropertyName,
        QgsProperty.fromExpression('"display_rule.model2d.model"'),
    )

    raster_layer.setDataDefinedProperty(
        QgsSymbolLayer.PropertyAngle,
        QgsProperty.fromExpression('coalesce("display_rule.model2d.bearing", 0)'),
    )

    # Width in map units based on the display_rule.model2d.width_meters field
    raster_layer.setDataDefinedProperty(
        QgsSymbolLayer.PropertyWidth,
        QgsProperty.fromExpression(
            """
if(
    "display_rule.model2d.model" IS NOT NULL AND "display_rule.model2d.model" LIKE '%.svg',
    0,
    coalesce("display_rule.model2d.width_meters", 5)
)
"""
        ),
    )

    # Height in map units based on the display_rule.model2d.height_meters field
    raster_layer.setDataDefinedProperty(
        QgsSymbolLayer.PropertyHeight,
        QgsProperty.fromExpression(
            """
if(
    "display_rule.model2d.model" IS NOT NULL AND "display_rule.model2d.model" LIKE '%.svg',
    0,
    coalesce("display_rule.model2d.height_meters", 5)
)
"""
        ),
    )

    # Set size unit to map units (meters)
    raster_layer.setSizeUnit(
        # Qgis.RenderUnit.MapUnits
        Qgis.RenderUnit.MetersInMapUnits
    )

    return raster_layer


def add_raster_symbol(layers):
    """
    Add raster symbols to layers by adding raster marker layers to their own geometry generators
    based on display_rule.model2d.model with scaling and rotation.
    Uses width_meters and height_meter parameters for proportional sizing.

    Args:
        layers: List of vector layers to add the raster symbols to
    """
    if not read_bool_setting("ADD_2DMODEL_STYLING"):
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
            # For rule-based renderers, modify each rule's symbol
            root_rule = renderer.rootRule()
            for child_rule in root_rule.children():
                if child_rule.symbol():
                    # Add raster with its own geometry generator
                    add_raster_with_geometry_generator(child_rule.symbol())
                    modified = True

            # Create a new renderer with the modified rules
            new_renderer = renderer.clone()
            layer.setRenderer(new_renderer)

        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            # For categorized renderers, add to each category symbol
            categories = []
            for category in renderer.categories():
                if category.symbol():
                    symbol = category.symbol().clone()
                    add_raster_with_geometry_generator(symbol)
                    # Create a new category with the modified symbol
                    new_category = QgsRendererCategory(
                        category.value(), symbol, category.label()
                    )
                    categories.append(new_category)
                    modified = True

            # Also modify source symbol if present
            source_symbol = None
            if renderer.sourceSymbol():
                source_symbol = renderer.sourceSymbol().clone()
                add_raster_with_geometry_generator(source_symbol)

            # Create a new renderer with the modified categories
            if categories:
                new_renderer = QgsCategorizedSymbolRenderer(
                    renderer.classAttribute(), categories
                )

                if source_symbol:
                    new_renderer.setSourceSymbol(source_symbol)

                layer.setRenderer(new_renderer)

        else:
            # For simple renderers like single symbol renderer
            symbol = renderer.symbol()
            if symbol:
                # Add raster with its own geometry generator
                add_raster_with_geometry_generator(symbol)

                # Create a new renderer with the modified symbol
                new_renderer = renderer.clone()
                new_renderer.setSymbol(symbol)
                layer.setRenderer(new_renderer)

                modified = True
            else:
                logger.error(f"Symbol not found for layer {layer.name()}")

        # Trigger layer updates if modified
        if modified:
            layer.triggerRepaint()
            layer.emitStyleChanged()
            logger.warning(f"Added raster symbol layer to layer '{layer.name()}'")
