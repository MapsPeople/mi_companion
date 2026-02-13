from qgis.core import (
    QgsExpression,
)


two_color_gradient_feature_m_start = QgsExpression(
    """
  ramp_color(
    'Turbo',
    scale_linear(
      m_max($geometry),
      aggregate(@layer,'min',m_min(@geometry)),
      aggregate(@layer,'max',m_max(@geometry)),
      0,
      1
    )
  )
"""
)
two_color_gradient_feature_m_end = QgsExpression(
    """
  ramp_color(
    'Turbo',
    scale_linear(
      m_min($geometry),
      aggregate(@layer,'min',m_min(@geometry)),
      aggregate(@layer,'max',m_max(@geometry)),
      0,
      1
    )
  )
"""
)

mean_m_expression = QgsExpression("(m_min(@geometry)+m_max(@geometry)) / 2")

layer_normalised_mean_m = QgsExpression(
    """
mean(
  m_min($geometry),
  m_max($geometry)
)/(
  aggregate(
    @layer,
    'max',
    m_max($geometry)
  )-aggregate(
    @layer,
    'min',
    m_min($geometry)
  )
)
"""
)
