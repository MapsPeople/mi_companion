# noinspection PyUnresolvedReferences
from qgis.core import (
    Qgis,
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
    QgsRuleBasedRenderer,
    QgsSymbol,
    QgsSymbolLayer,
    QgsWkbTypes,
)

HEX_COLOR_POLY_FILL_EXPRESSION = QgsProperty.fromExpression(
    r"""
with_variable('i',
  set_color_part(
    "display_rule.polygon.fill_color",
    'alpha',
    "display_rule.polygon.fill_opacity"*255
  ),
  if(
    @i IS 'array',
    with_variable('a',
      with_variable(
        'numb',
        string_to_array(  @i    ),
        array_foreach (
          @numb,
          with_variable(
            'hex',
            array_cat(
              generate_series(0,9),
              array('A','B','C','D','E','F')
            ),
            @hex [floor (@element/16)] || @hex [@element%16]
          )
        )
      ),
      concat('#',@a[-1],@a[0],@a[1],@a[2])
    ),
    with_variable(
      'hex',
      array_cat(
          generate_series(0,9),
          array('A','B','C','D','E','F')
      ),
      concat(
        '#',
        array_to_string (
          array_foreach (
            array ('alpha','red','green','blue'),
            with_variable(
                'colo',
                color_part (@i, @element),
                @hex[floor(@colo/16)] || @hex[@colo%16]
            )
          ),
          ''
        )
      )
    )
  )
)
"""
)
ROT_AND_SCALE_GEOMETRY_LINE_GENERATOR_EXPRESSION = r"""
with_variable('p',
  make_point("anchor_x","anchor_y"),
  rotate(
    make_line(
      @p,
      translate(
        @p,
        0,
        "display_rule.model3d.scale"
      )
    ),
    "display_rule.model3d.rotation_z",
    @p,
    false
  )
)
"""


ANCHOR_GEOMETRY_GENERATOR_EXPRESSION = """
if(
  "anchor_x" is NULL OR "anchor_y" is NULL OR "anchor_x" IS '' OR "anchor_y" IS '',
  centroid(@geometry),
  make_point("anchor_x","anchor_y")
)

"""


ANCHOR_GEOMETRY_GENERATOR_EXPRESSION_COMPONENT = (
    "{component}(" + ANCHOR_GEOMETRY_GENERATOR_EXPRESSION + ")"
)

RESET_ANCHOR_TO_CENTROID_IF_MOVED_OUTSIDE_GEOMETRY = """
with_variable(
  'anchor',
  make_point("anchor_x","anchor_y"),
  if(
    is_empty_or_null(@anchor),
    centroid( @geometry ),
    if(
      within(@anchor,@geometry),
        @anchor,
        centroid( @geometry )
    )
  )
)
"""

RESET_ANCHOR_TO_CENTROID_IF_MOVED_OUTSIDE_GEOMETRY_COMPONENT = (
    "{component}(" + RESET_ANCHOR_TO_CENTROID_IF_MOVED_OUTSIDE_GEOMETRY + ")"
)


NAME_MUST_NOT_NULL_AND_NOT_EMPTY_VALIDATION_EXPRESSION = """
"{field_name}" IS NOT NULL AND "{field_name}" IS NOT ''
"""

IF_NAME_IS_POPULATED_KEEP_IT_OTHERWISE_GET_LOCATION_TYPE_NAME = """
if("{field_name}","{field_name}",represent_value(location_type))
"""

DEFAULT_NAME_GET_LOCATION_TYPE_NAME_EXPRESSION = r"""
string_to_array( represent_value(location_type) , '>')[-1]
"""


def get_hierarchical_lookup_field_expression(
    current_layer,
    look_up_field_name: str = "display_rule.model2d.model",
    first_level_reference_field_name="location_type",
    second_level_referenced_field_name="admin_id",
    fallback_layer_name="solution_config",
):
    """
    Creates a QGIS expression that looks up the 2D model from location_types layer
    dynamically finding the layer referenced by the relation editor widget.
    Supports both RelationReference and ValueRelation widget types.
    """
    # Add the missing imports
    from qgis.core import QgsProject

    if not current_layer:
        raise Exception("No current layer provided")

    # Get the field index and widget setup
    field_idx = current_layer.fields().indexFromName(first_level_reference_field_name)

    if field_idx < 0:
        raise Exception(f"Field {first_level_reference_field_name} not found in layer")

    widget_setup = current_layer.editorWidgetSetup(field_idx)
    config = widget_setup.config()

    # Extract referenced layer ID based on widget type
    referenced_layer_id = None
    widget_type = widget_setup.type()

    if widget_type == "RelationReference" and "ReferencedLayerId" in config:
        referenced_layer_id = config["ReferencedLayerId"]
    elif widget_type == "ValueRelation" and "LayerId" in config:
        referenced_layer_id = config["LayerId"]
    elif "layer" in config:  # Fallback for older QGIS versions or custom widgets
        referenced_layer_id = config["layer"]
    else:
        # Try to find location_types layer by name
        for layer in QgsProject.instance().mapLayers().values():
            if "location_types" in layer.name().lower():
                referenced_layer_id = layer.id()
                break
        else:
            raise Exception(f"A location type reference layer was not found!")

    return f"""
with_variable(
  'look_up_field_name',
  '{look_up_field_name}',
 if(
    attribute(@look_up_field_name),
    attribute(@look_up_field_name),
    with_variable(
      'lt_2d_model',
      attribute(
        get_feature(
          '{referenced_layer_id}',
          '{second_level_referenced_field_name}',
          "{first_level_reference_field_name}"
        ),
        @look_up_field_name
      ),
      with_variable(
        'fallback_2d_model',
        attribute(
          '{fallback_layer_name}',
          get_feature_by_id(
            '{fallback_layer_name}',
            1
          ),
          @look_up_field_name
        ),
        if(
        @lt_2d_model,
        @lt_2d_model,
        if(
         @fallback_2d_model,
         @fallback_2d_model,
         NULL
        )
      )
     )
   )
 )
)
"""
