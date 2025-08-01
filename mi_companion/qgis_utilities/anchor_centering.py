import logging
from typing import Iterable

# noinspection PyUnresolvedReferences
from qgis.core import (
    Qgis,
    QgsDefaultValue,
    QgsFieldConstraints,
)

from mi_companion.constants import ONLY_RESET_ANCHOR_IF_OUTSIDE
from .expressions import (
    RESET_ANCHOR_TO_CENTROID_COMPONENT,
    RESET_ANCHOR_TO_CENTROID_IF_MOVED_OUTSIDE_GEOMETRY_COMPONENT,
)

__all__ = ["auto_center_anchors_when_outside"]


logger = logging.getLogger(__name__)


def auto_center_anchors_when_outside(layers: Iterable) -> None:
    for layers_inner in layers:

        for c, v in {"anchor_x": "x", "anchor_y": "y"}.items():
            fields = layers_inner.fields()

            # Find name fields, including translations
            for field_idx in range(fields.count()):
                field_name = fields.at(field_idx).name()

                if c in field_name:
                    layers_inner.setFieldConstraint(
                        field_idx,
                        QgsFieldConstraints.ConstraintNotNull,
                        QgsFieldConstraints.ConstraintStrengthHard,
                    )

                    layers_inner.setFieldConstraint(
                        field_idx,
                        QgsFieldConstraints.ConstraintExpression,
                        QgsFieldConstraints.ConstraintStrengthHard,
                    )

                    default_expression = RESET_ANCHOR_TO_CENTROID_COMPONENT

                    if ONLY_RESET_ANCHOR_IF_OUTSIDE:
                        default_expression = (
                            RESET_ANCHOR_TO_CENTROID_IF_MOVED_OUTSIDE_GEOMETRY_COMPONENT
                        )

                    # Set default value for the name field
                    default_value = QgsDefaultValue(
                        default_expression.format(component=v),
                        applyOnUpdate=True,
                    )
                    layers_inner.setDefaultValueDefinition(field_idx, default_value)

                    try:
                        # Set policy to use default value when splitting
                        layers_inner.setFieldSplitPolicy(
                            field_idx, Qgis.FieldDomainSplitPolicy.GeometryRatio
                        )
                    except Exception as e:
                        logger.warning(
                            "QgsVectorLayer.setFieldSplitPolicy is only available in QGIS >=3.30.0, please upgrade your QGIS to fix this"
                        )

                    try:
                        # Set policy to use default value when merging
                        layers_inner.setFieldMergePolicy(
                            field_idx, Qgis.FieldDomainMergePolicy.DefaultValue
                        )
                    except Exception as e:
                        logger.warning(
                            "QgsVectorLayer.setFieldMergePolicy is only available in QGIS >=3.44.0, please upgrade your QGIS to fix this"
                        )

                    try:
                        # Set policy to use default value when duplicating
                        layers_inner.setFieldDuplicatePolicy(
                            field_idx, Qgis.FieldDuplicatePolicy.Duplicate
                        )
                    except Exception as e:
                        logger.warning(
                            "QgsVectorLayer.setFieldDuplicatePolicy is only available in QGIS >=3.38.0, please upgrade your QGIS to fix this"
                        )
