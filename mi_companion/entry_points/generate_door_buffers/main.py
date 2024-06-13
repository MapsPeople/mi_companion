#!/usr/bin/python
import logging

import shapely
from jord.geometric_analysis import buffer_principal_axis
from jord.shapely_utilities import dilate, is_multi
from jord.qlive_utilities import add_shapely_layer

logger = logging.getLogger(__name__)


def run(*, buffer_distance: float = 0.01, only_active_layer: bool = True) -> None:
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
                door_geom = {}
                door_buffers = {}

                for feature in iter(selected_features):
                    logger.info(f"Randomizing {feature.id()}")

                    feature_geom = feature.geometry()
                    if feature_geom is not None:
                        geom_wkt = feature_geom.asWkt()
                        if geom_wkt is not None:
                            geom_shapely = shapely.from_wkt(geom_wkt)
                            if geom_shapely is not None:
                                door_geom[feature.id()] = geom_shapely

                door_geoms = dilate(
                    shapely.unary_union(list(door_geom.values())),
                    distance=buffer_distance,
                )
                if is_multi(door_geoms):
                    for ith_door, door_geom in enumerate(door_geoms.geoms):
                        door_buffers[ith_door] = buffer_principal_axis(door_geom)
                else:
                    door_buffers[0] = buffer_principal_axis(door_geom)

                graph_lines_layer = add_shapely_layer(
                    qgis_instance_handle=QgsProject.instance(),
                    geoms=door_buffers.values(),
                    name="door_buffers",
                    visible=True,
                    crs=f"EPSG:3857",
                )

            else:
                logger.error(f"Please select feature in the layer")

            # layer.commitChanges()
        else:
            logger.error(f"Skipping layer {layer.name()} as it had no selected feature")
