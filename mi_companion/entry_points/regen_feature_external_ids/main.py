#!/usr/bin/python
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def randomize_fields_selected_features(feature, field_name: str) -> Any:  # QgsFeature
    """https://qgis.org/pyqgis/3.2/core/Feature/QgsFeature.html#qgis.core.QgsFeature.setAttribute
        Regarding layer.updateFeature()
    Always try to avoid the QgsVectorLayer.updateFeature() method. It's less efficient than
    changeAttributeValue().

    From the docs:

    This method needs to query the underlying data provider to fetch the feature with matching QgsFeature::id(
    ) on every call. Depending on the underlying data source this can be slow to execute. Consider using the
    more efficient changeAttributeValue() or changeGeometry() methods instead.
    """
    if feature is None:
        logger.error(f"feature was None")
        return

    field_idx = feature.fieldNameIndex(field_name)

    if field_idx >= 0:
        logger.info(f"Randomizing {field_name}:{field_idx}")

        feature.setAttribute(field_idx, uuid.uuid4().hex)

        return feature
    else:
        logger.error(f"Did not find {field_name} in {feature.fields()}")


def run(*, field_name: str = "external_id", only_active_layer: bool = False) -> None:
    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    # noinspection PyUnresolvedReferences
    from qgis.core import QgsProject

    if only_active_layer:
        if False:
            layers = list(iface.activeLayer())
        else:
            layers = list(
                iface.layerTreeView().selectedLayers()
            )  # TODO: MAYBE use this?
    else:
        layers = list(QgsProject.instance().mapLayers().values())

    if len(layers) == 0:
        logger.error(f"No layers was given {layers}")

    for layer in layers:  # TODO: Only do this for already editing layers
        if layer.selectedFeatureCount() > 0:
            # layer.startEditing()  # TODO: Allow editing of not already editing layers?
            selected_features = layer.selectedFeatures()

            if len(selected_features) > 0:
                for feature in iter(selected_features):
                    logger.info(f"Randomizing {feature.id()}")
                    feature = randomize_fields_selected_features(feature, field_name)
                    layer.updateFeature(feature)
            else:
                logger.error(f"Please select feature in the layer")

            # layer.commitChanges()
        else:
            logger.error(f"Skipping layer {layer.name()} as it had no selected feature")
