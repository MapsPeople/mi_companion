#!/usr/bin/python
import logging

from mi_companion.utilities.validation import validate_venue

logger = logging.getLogger(__name__)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    Qgis,
)


def run() -> None:
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

    selected_nodes = iface.layerTreeView().selectedNodes()

    if len(selected_nodes) > 0:
        for n in iter(selected_nodes):
            validate_venue(n)
    else:
        logger.error(f"Number of selected nodes was {len(selected_nodes)}")
        logger.error(f"Please select node in the layer tree")
