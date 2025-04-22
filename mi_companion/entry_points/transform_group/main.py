#!/usr/bin/python
import logging
from pathlib import Path

from jord.qgis_utilities import (
    get_gcp_transformer_from_file,
    transform_sub_tree_features,
)

from mi_companion.constants import MI_EPSG_NUMBER
from mi_companion.mi_editor import get_target_crs_srsid
from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    Qgis,
)

SOURCE_CRS = QgsCoordinateReferenceSystem(MI_EPSG_NUMBER)
DEST_CRS = QgsCoordinateReferenceSystem(get_target_crs_srsid())
PRE_TRANSFORM = None

if False:  # TODO: Transform if not the same as GCPs!
    PRE_TRANSFORM = QgsCoordinateTransform(SOURCE_CRS, DEST_CRS, QgsProject.instance())

# FORWARD_TRANSFORM = QgsCoordinateTransform(DEST_CRS, SOURCE_CRS, QgsProject.instance())
# BACKWARD_TRANSFORM = QgsCoordinateTransform(DEST_CRS, SOURCE_CRS, QgsProject.instance())

__all__ = []


def run(
    *,
    gcp_points_file_path: Path,
    method: int = 1,
    # TODO: MAKE Method into a dropdown based on enum
) -> None:
    """
    Transform geometry for all features in the selected group

    WARNING! Settings -> Options -> MapsIndoor Beta -> "REPROJECT_SHAPES" must be set to "True"

    0: Linear:            Linear transform    ( min. 3 GCPs )
    1: Helmert:           Helmert transform   ( min. 3 GCPs )
    2: PolynomialOrder1:  Polynomial order 1  ( min. 3 GCPs )
    3: PolynomialOrder2:  Polyonmial order 2  ( min. 6 GCPs )
    4: PolynomialOrder3:  Polynomial order 3  ( min. 10 GCPs )
    5: ThinPlateSpline:   Thin plate splines
    6: Projective:        Projective
    65535:                InvalidTransform: Invalid transform


    :param gcp_points_file_path: The path to the file containing the GCPs
    :param method: Which method to use for the transformation
    :return:
    """

    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    # noinspection PyUnresolvedReferences
    from qgis.analysis import QgsGcpTransformerInterface

    assert gcp_points_file_path is not None

    assert gcp_points_file_path.exists()

    transformer = get_gcp_transformer_from_file(
        gcp_points_file_path, method=QgsGcpTransformerInterface.TransformMethod(method)
    )

    selected_nodes = iface.layerTreeView().selectedNodes()

    if len(selected_nodes) > 0:
        for n in iter(selected_nodes):
            transform_sub_tree_features(
                n, transformer=transformer, pre_transformer=PRE_TRANSFORM
            )
    else:
        logger.error(f"Number of selected nodes was {len(selected_nodes)}")
        logger.error(f"Please select node in the layer tree")
