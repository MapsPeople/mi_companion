#!/usr/bin/python
import logging
from pathlib import Path

from qgis.analysis import QgsGcpGeometryTransformer, QgsGcpTransformerInterface

from mi_companion.utilities.gcp_transformer_factory import get_gcp_transformer_from_file

logger = logging.getLogger(__name__)

__all__ = ["transform_features", "transform_sub_tree_features"]

from typing import Collection, Union, Any


def run(*, gcp_points_file_path: Path, method: int = 1) -> None:
    """
      Transform geometry for all features in the selected group

      Linear: Linear transform                0
      Helmert: Helmert transform              1
      PolynomialOrder1: Polynomial order 1    2
      PolynomialOrder2: Polyonmial order 2    3
      PolynomialOrder3: Polynomial order 3    4
      ThinPlateSpline: Thin plate splines     5
      Projective: Projective                  6
      InvalidTransform                    65535
    InvalidTransform: Invalid transform

      :param method:
      :param gcp_points_file_path:
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
            transform_sub_tree_features(n, transformer=transformer)
    else:
        logger.error(f"Number of selected nodes was {len(selected_nodes)}")
        logger.error(f"Please select node in the layer tree")


def transform_sub_tree_features(
    selected_nodes: Union[Any, Collection[Any]], transformer: QgsGcpGeometryTransformer
) -> None:
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsLayerTreeNode

    if isinstance(selected_nodes, QgsLayerTreeLayer):
        transform_features(selected_nodes, transformer=transformer)
    elif isinstance(selected_nodes, QgsLayerTreeGroup):
        transform_sub_tree_features(selected_nodes.children(), transformer=transformer)
    elif isinstance(selected_nodes, QgsLayerTreeNode):
        if selected_nodes.nodeType() == QgsLayerTreeNode.NodeGroup:
            transform_sub_tree_features(
                selected_nodes.children(), transformer=transformer
            )
        else:
            logger.error(
                f"Node {selected_nodes} was not supported in transform_sub_tree_features, skipping"
            )
    else:
        if len(selected_nodes) == 0:
            logger.error(
                f"'Number of selected nodes was {len(selected_nodes)}, please supply some"
            )
            return

        for group in iter(selected_nodes):
            if isinstance(group, QgsLayerTreeLayer):
                transform_features(group, transformer=transformer)
            elif isinstance(group, QgsLayerTreeGroup):
                transform_sub_tree_features(group.children(), transformer=transformer)
            elif isinstance(group, QgsLayerTreeNode):
                if group.nodeType() == QgsLayerTreeNode.NodeGroup:
                    transform_sub_tree_features(
                        group.children(), transformer=transformer
                    )
                else:
                    logger.error(
                        f"Node {group} was not supported in transform_sub_tree_features, skipping"
                    )
            else:
                logger.error(
                    f"Node {group} was not supported in transform_sub_tree_features, skipping"
                )


def transform_features(
    tree_layer: Any, transformer: QgsGcpGeometryTransformer
) -> None:  #: QgsLayerTreeLayer
    """

    :param transformer:
    :param tree_layer:
    :return:
    """

    if tree_layer is None:
        logger.error(f"Tree layer was None")
        return

    layer = tree_layer.layer()

    if not layer.isValid():
        logger.error(f"{tree_layer.layer().name()} is not valid!")
        return

    layer.startEditing()

    logger.warning(
        f"Transforming geometry of layer with name: {tree_layer.layer().name()}"
    )

    for idx, feat in enumerate(layer.getFeatures()):
        assert feat.hasGeometry()

        geom, ok = transformer.transform(feat.geometry())
        if not ok:
            logger.error(
                f"Error while transforming {geom} in layer {tree_layer.layer().name()}"
            )
        feat.setGeometry(geom)
        layer.updateFeature(feat)

    layer.endEditCommand()
    layer.commitChanges()
    layer.triggerRepaint()
