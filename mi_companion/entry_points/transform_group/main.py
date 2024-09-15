#!/usr/bin/python
import logging
from pathlib import Path

from jord.qgis_utilities import (
    get_gcp_transformer_from_file,
    transform_sub_tree_features,
)
from qgis.analysis import QgsGcpTransformerInterface

from mi_companion.mi_editor.conversion.projection import GDS_EPSG_NUMBER, MI_EPSG_NUMBER

logger = logging.getLogger(__name__)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    Qgis,
)

SOURCE_CRS = QgsCoordinateReferenceSystem(MI_EPSG_NUMBER)
DEST_CRS = QgsCoordinateReferenceSystem(GDS_EPSG_NUMBER)
FORWARD_TRANSFORM = None

if False:  # TODO: Transform if not the same as GCPs!
    FORWARD_TRANSFORM = QgsCoordinateTransform(
        SOURCE_CRS, DEST_CRS, QgsProject.instance()
    )

# FORWARD_TRANSFORM = QgsCoordinateTransform(DEST_CRS, SOURCE_CRS, QgsProject.instance())
# BACKWARD_TRANSFORM = QgsCoordinateTransform(DEST_CRS, SOURCE_CRS, QgsProject.instance())


def run(*, gcp_points_file_path: Path, method: int = 1) -> None:
    """
    Transform geometry for all features in the selected group

    0: Linear: Linear transform
    1: Helmert: Helmert transform
    2: PolynomialOrder1: Polynomial order 1
    3: PolynomialOrder2: Polyonmial order 2
    4: PolynomialOrder3: Polynomial order 3
    5: ThinPlateSpline: Thin plate splines
    6: Projective: Projective
    65535: InvalidTransform: Invalid transform


    :param gcp_points_file_path:
    :param method:
    :return:
    """

    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    assert gcp_points_file_path is not None

    assert gcp_points_file_path.exists()

    transformer = get_gcp_transformer_from_file(
        gcp_points_file_path, method=QgsGcpTransformerInterface.TransformMethod(method)
    )

    selected_nodes = iface.layerTreeView().selectedNodes()

    if len(selected_nodes) > 0:
        for n in iter(selected_nodes):
            transform_sub_tree_features(
                n, transformer=transformer, pre_transformer=FORWARD_TRANSFORM
            )
    else:
        logger.error(f"Number of selected nodes was {len(selected_nodes)}")
        logger.error(f"Please select node in the layer tree")
