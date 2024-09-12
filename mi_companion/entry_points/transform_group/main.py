#!/usr/bin/python
import logging
from operator import xor
from pathlib import Path

from PyQt5.QtGui import QTransform

logger = logging.getLogger(__name__)

__all__ = ["transform_features", "transform_sub_tree_features"]

from typing import Collection, Optional, Union, Any


def run(
    *, wld_file_path: Optional[Path] = None, gcp_points_file_path: Optional[Path] = None
) -> None:
    """


    Transform geometry for all features in the selected group



    :param wld_file_path:
    :param gcp_points_file_path:
    :return:
    """

    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    assert xor(wld_file_path is not None, gcp_points_file_path is not None)

    if gcp_points_file_path is not None:
        assert gcp_points_file_path.exists()
        with open(gcp_points_file_path) as gcp_points_file:
            # gcp_points = json.load(gcp_points_file)
            ...
            transform = None
    else:
        """

            WLD -- ESRI World File
        A world file file is a plain ASCII text file consisting of six values separated by newlines. The format is:

        pixel X size
        rotation about the Y axis (usually 0.0)
        rotation about the X axis (usually 0.0)
        negative pixel Y size
        X coordinate of upper left pixel center
        Y coordinate of upper left pixel center

        For example:

        60.0000000000
        0.0000000000
        0.0000000000
        -60.0000000000
        440750.0000000000
        3751290.0000000000

        """

        assert wld_file_path is not None
        assert wld_file_path.exists()
        with open(wld_file_path) as wld_file:
            # from PyQt5.QtGui import QMatrix4x4, QTransform
            m32 = (float(c) for c in wld_file.readlines())

            # 	QTransform(qreal m11, qreal m12, qreal m21, qreal m22, qreal dx, qreal dy)
            transform = QTransform(*m32)

            # def setMatrix(m11, m12, m21, m22, dx, dy)
            # gcp_points = json.load(wld_file)

    selected_nodes = iface.layerTreeView().selectedNodes()

    if len(selected_nodes) > 0:
        for n in iter(selected_nodes):
            transform_sub_tree_features(n, transform=transform)
    else:
        logger.error(f"Number of selected nodes was {len(selected_nodes)}")
        logger.error(f"Please select node in the layer tree")


def transform_sub_tree_features(
    selected_nodes: Union[Any, Collection[Any]], transform: QTransform
) -> None:
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsLayerTreeNode

    if isinstance(selected_nodes, QgsLayerTreeLayer):
        transform_features(selected_nodes, transform=transform)
    elif isinstance(selected_nodes, QgsLayerTreeGroup):
        transform_sub_tree_features(selected_nodes.children(), transform=transform)
    elif isinstance(selected_nodes, QgsLayerTreeNode):
        if selected_nodes.nodeType() == QgsLayerTreeNode.NodeGroup:
            transform_sub_tree_features(selected_nodes.children(), transform=transform)
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
                transform_features(group, transform=transform)
            elif isinstance(group, QgsLayerTreeGroup):
                transform_sub_tree_features(group.children(), transform=transform)
            elif isinstance(group, QgsLayerTreeNode):
                if group.nodeType() == QgsLayerTreeNode.NodeGroup:
                    transform_sub_tree_features(group.children(), transform=transform)
                else:
                    logger.error(
                        f"Node {group} was not supported in transform_sub_tree_features, skipping"
                    )
            else:
                logger.error(
                    f"Node {group} was not supported in transform_sub_tree_features, skipping"
                )


def transform_features(
    tree_layer: Any, transform: QTransform
) -> None:  #: QgsLayerTreeLayer
    """

    :param transform:
    :param tree_layer:
    :return:
    """

    from qgis.core import QgsFeature

    if tree_layer is None:
        logger.error(f"Tree layer was None")
        return
    # logger.info(f'Randomizing {field_name} in {tree_layer.layer().name()}')

    layer = tree_layer.layer()

    if not layer.isValid():
        logger.error(f"{tree_layer.layer().name()} is not valid!")
        return

    layer.startEditing()
    # layer.beginEditCommand(f"Regenerate {field_name}")
    logger.warning(
        f"Transforming geometry of layer with name: {tree_layer.layer().name()}"
    )

    for idx, feat in enumerate(layer.getFeatures()):
        feat: QgsFeature

        assert feat.hasGeometry()
        geom = feat.geometry()
        transformation_res = geom.transform(transform)
        # print(transformation_res)
        # logger.warning(f'{transformation_res}')

        feat.setGeometry(geom)
        layer.updateFeature(feat)

        # layer.changeGeometry(idx, geom)

    # layer.rollBack()
    layer.endEditCommand()
    layer.commitChanges()
    layer.triggerRepaint()
