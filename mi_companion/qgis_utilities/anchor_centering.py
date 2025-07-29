from mi_companion.qgis_utilities import (
    RESET_ANCHOR_TO_CENTROID_IF_MOVED_OUTSIDE_GEOMETRY_COMPONENT,
)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsProject,
    QgsFieldConstraints,
    QgsDefaultValue,
    QgsEditorWidgetSetup,
)

# noinspection PyUnresolvedReferences
from qgis.core import Qgis, QgsGeometry, QgsMessageLog

__all__ = ["auto_center_anchors_when_outside"]


def auto_center_anchors_when_outside(layers):
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

                    # Set default value for the name field
                    default_value = QgsDefaultValue(
                        RESET_ANCHOR_TO_CENTROID_IF_MOVED_OUTSIDE_GEOMETRY_COMPONENT.format(
                            component=v
                        ),
                        applyOnUpdate=True,
                    )
                    layers_inner.setDefaultValueDefinition(field_idx, default_value)

                    # Set policy to use default value when splitting
                    layers_inner.setFieldSplitPolicy(
                        field_idx, Qgis.FieldDomainSplitPolicy.GeometryRatio
                    )

                    # Set policy to use default value when merging
                    layers_inner.setFieldMergePolicy(
                        field_idx, Qgis.FieldDomainMergePolicy.DefaultValue
                    )

                    # Set policy to use default value when duplicating
                    layers_inner.setFieldDuplicatePolicy(
                        field_idx, Qgis.FieldDuplicatePolicy.Duplicate
                    )
