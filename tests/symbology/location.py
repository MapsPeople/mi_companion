# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsField,
    QgsFillSymbol,
    QgsGeometry,
    QgsLayerTree,
    QgsLayerTreeModel,
    QgsProject,
    QgsProject,
    QgsRasterLayer,
    QgsRuleBasedRenderer,
    QgsVectorLayer,
    QgsVectorLayer,
)


def apply_display_rule_styling(layer, location_type_ref_layer):
    pass


def test_apply_display_rule_styling(qgis_app):
    """Test the symbology implementation for display rules."""
    # Create a mock layer
    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Test Layer", "memory")
    provider = layer.dataProvider()
    provider.addAttributes(
        [
            QgsField("display_rule.polygon.fill_color", QVariant.String),
            QgsField("display_rule.polygon.stroke_color", QVariant.String),
            QgsField("location_type", QVariant.String),
        ]
    )
    layer.updateFields()

    # Add mock features
    feature = QgsFeature(layer.fields())
    feature.setAttributes(["#ff0000", "#000000", "type_1"])
    feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"))
    provider.addFeatures([feature])
    layer.updateExtents()

    # Mock location type reference layer
    location_type_ref_layer = QgsVectorLayer(
        "Polygon?crs=EPSG:4326", "Location Type Layer", "memory"
    )
    ref_provider = location_type_ref_layer.dataProvider()
    ref_provider.addAttributes(
        [
            QgsField("admin_id", QVariant.String),
            QgsField("display_rule.polygon.fill_color", QVariant.String),
            QgsField("display_rule.polygon.stroke_color", QVariant.String),
        ]
    )
    location_type_ref_layer.updateFields()

    ref_feature = QgsFeature(location_type_ref_layer.fields())
    ref_feature.setAttributes(["type_1", "#00ff00", "#0000ff"])
    ref_feature.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"))
    ref_provider.addFeatures([ref_feature])
    location_type_ref_layer.updateExtents()

    # Apply symbology
    apply_display_rule_styling(layer, location_type_ref_layer)

    # Verify renderer
    renderer = layer.renderer()
    assert isinstance(renderer, QgsRuleBasedRenderer)

    # Check rules
    root_rule = renderer.rootRule()
    assert len(root_rule.children()) == 2  # Individual style and fallback style

    # Verify individual style rule
    individual_rule = root_rule.children()[0]
    assert individual_rule.filterExpression() == (
        '"display_rule.polygon.fill_color" IS NOT NULL AND '
        '"display_rule.polygon.stroke_color" IS NOT NULL'
    )
    individual_symbol = individual_rule.symbol()
    assert isinstance(individual_symbol, QgsFillSymbol)
    assert individual_symbol.color().name() == "#ff0000"
    assert individual_symbol.borderColor().name() == "#000000"

    # Verify fallback style rule
    fallback_rule = root_rule.children()[1]
    assert fallback_rule.filterExpression() == "ELSE"
    fallback_symbol = fallback_rule.symbol()
    assert isinstance(fallback_symbol, QgsFillSymbol)
    assert fallback_symbol.color().name() == "#00ff00"
    assert fallback_symbol.borderColor().name() == "#0000ff"
