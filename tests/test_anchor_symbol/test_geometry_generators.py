import pytest
from unittest.mock import MagicMock, patch

from mi_companion.mi_editor.conversion.styling.anchor_symbol import (
    _rule_matches_location_types,
    add_rotation_scale_geometry_generator,
    remove_rotation_scale_geometry_generator,
)

# Tests for _rule_matches_location_types
def test_rule_matches_location_types_with_no_filter():
    rule = MagicMock()
    rule.filterExpression.return_value = ""
    assert _rule_matches_location_types(rule, {"building", "tree"}) is True


def test_rule_matches_location_types_when_match_found():
    rule = MagicMock()
    rule.filterExpression.return_value = '"location_type" = \'building\''
    assert _rule_matches_location_types(rule, {"building", "tree"}) is True


def test_rule_matches_location_types_when_no_match():
    rule = MagicMock()
    rule.filterExpression.return_value = '"location_type" = \'road\''
    assert _rule_matches_location_types(rule, {"building", "tree"}) is False


def test_rule_matches_location_types_with_none_filter_expression():
    rule = MagicMock()
    rule.filterExpression.return_value = None
    assert _rule_matches_location_types(rule, {"building"}) is True


# add_rotation_scale_geometry_generator tests
@pytest.fixture
def mock_layer():
    """Create a mock QgsVectorLayer-like object."""
    layer = MagicMock()
    layer.name.return_value = "mock_layer"
    return layer


@patch("mi_companion.mi_editor.conversion.styling.anchor_symbol.add_anchor_and_rot_scl_geometry_generators_to_symbol")
def test_add_rotation_scale_geometry_generator_with_rule_based(mock_add_symbol, mock_layer):
    # Mock a rule-based renderer with one rule and symbol
    mock_symbol = MagicMock()
    mock_rule = MagicMock()
    mock_rule.symbol.return_value = mock_symbol
    mock_rule.filterExpression.return_value = '"location_type" = \'building\''
    root_rule = MagicMock()
    root_rule.children.return_value = [mock_rule]

    renderer = MagicMock()
    renderer.rootRule.return_value = root_rule
    renderer.__class__.__name__ = "QgsRuleBasedRenderer"

    mock_layer.renderer.return_value = renderer

    with patch("your_module_name.QgsRuleBasedRenderer", type(renderer)):
        add_rotation_scale_geometry_generator([mock_layer], {"building"})

    mock_add_symbol.assert_called_once_with(mock_symbol.clone.return_value)
    mock_layer.triggerRepaint.assert_called_once()
    mock_layer.emitStyleChanged.assert_called_once()


@patch("mi_companion.mi_editor.conversion.styling.anchor_symbol.add_anchor_and_rot_scl_geometry_generators_to_symbol")
def test_add_rotation_scale_geometry_generator_with_no_layers(mock_add_symbol):
    add_rotation_scale_geometry_generator([], {"building"})
    mock_add_symbol.assert_not_called()


@patch("mi_companion.mi_editor.conversion.styling.anchor_symbol.add_anchor_and_rot_scl_geometry_generators_to_symbol")
def test_add_rotation_scale_geometry_generator_with_null_renderer(mock_add_symbol, mock_layer):
    mock_layer.renderer.return_value = None
    add_rotation_scale_geometry_generator([mock_layer], {"building"})
    mock_add_symbol.assert_not_called()


# remove_rotation_scale_geometry_generator tests
@patch("mi_companion.mi_editor.conversion.styling.anchor_symbol.remove_anchor_and_rot_scl_geometry_generators_from_symbol")
def test_remove_rotation_scale_geometry_generator_rule_based(mock_remove_symbol, mock_layer):
    mock_remove_symbol.return_value = True

    mock_symbol = MagicMock()
    mock_rule = MagicMock()
    mock_rule.symbol.return_value = mock_symbol
    mock_rule.filterExpression.return_value = '"location_type" = \'building\''

    root_rule = MagicMock()
    root_rule.children.return_value = [mock_rule]

    renderer = MagicMock()
    renderer.rootRule.return_value = root_rule
    renderer.__class__.__name__ = "QgsRuleBasedRenderer"

    mock_layer.renderer.return_value = renderer

    with patch("mi_companion.mi_editor.conversion.styling.anchor_symbol.QgsRuleBasedRenderer", type(renderer)):
        remove_rotation_scale_geometry_generator([mock_layer], {"building"})

    mock_remove_symbol.assert_called_once_with(mock_symbol)
    mock_layer.triggerRepaint.assert_called_once()
    mock_layer.emitStyleChanged.assert_called_once()


def test_remove_rotation_scale_geometry_generator_with_no_layers():
    remove_rotation_scale_geometry_generator([], {"building"})  # should not raise
