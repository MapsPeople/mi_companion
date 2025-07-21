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
  "anchor_x" is NULL OR "anchor_y" is NULL,
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
