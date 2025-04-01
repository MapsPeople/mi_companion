import logging
from typing import Any, Collection, Dict

import shapely

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

from integration_system.mi import MIOperation
from integration_system.model import (
    DIFFERENCE_GROUP_NAME,
    NEXT_DIFF_ITEM_INDICATOR,
    SHAPELY_DIFFERENCE_DESCRIPTION,
    Solution,
)
from mi_companion import MI_EPSG_NUMBER

__all__ = ["show_differences", "extract_operation_difference_geometry"]

logger = logging.getLogger(__name__)


def show_differences(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    solution_name: str,
    operations: Collection[MIOperation],
) -> None:
    """

    :param qgis_instance_handle:
    :param solution:
    :param solution_name:
    :param operations:
    :return:
    """
    mi_db_difference_group = (
        QgsProject.instance().layerTreeRoot().findGroup(DIFFERENCE_GROUP_NAME)
    )

    if not mi_db_difference_group:  # did not find the group
        mi_db_difference_group = (
            QgsProject.instance().layerTreeRoot().insertGroup(0, DIFFERENCE_GROUP_NAME)
        )

    solution_difference_group = mi_db_difference_group.findGroup(solution_name)

    if not solution_difference_group:  # did not find the group
        solution_difference_group = mi_db_difference_group.insertGroup(0, solution_name)

    venue = next(iter(solution.venues))
    venue_diff_name = venue.name

    venue_difference_group = solution_difference_group.findGroup(venue_diff_name)

    if venue_difference_group:  # Found the group
        for node in [
            child
            for child in venue_difference_group.children()
            # if child.nodeType() == 0
        ]:
            venue_difference_group.removeChildNode(node)
    else:  # did not find the group
        venue_difference_group = solution_difference_group.insertGroup(
            0, venue_diff_name
        )

    differences = {}
    for ith, o in enumerate(operations):
        if SHAPELY_DIFFERENCE_DESCRIPTION in o.context:
            extract_operation_difference_geometry(differences, o, f"operation{ith}")

    try:
        import geopandas

        df = geopandas.GeoDataFrame(
            {"op_ith": differences.keys(), "geometry": differences.values()},
            crs=f"EPSG:{MI_EPSG_NUMBER}",
            geometry="geometry",
        )
        from jord.qlive_utilities import add_dataframe_layer

        add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=df,
            geometry_column="geometry",
            name=f"Operation differences",
            group=venue_difference_group,
            crs=f"EPSG:{MI_EPSG_NUMBER}",
        )

    except Exception as e:  # TODO: HANDLE Mixed GEOM TYPES!
        logger.error(e)


def extract_operation_difference_geometry(
    differences: Dict[str, Any], o: MIOperation, operation_ith: str
):
    """

    :param differences:
    :param o:
    :param operation_ith:
    :return:
    """
    from jord.shapely_utilities import is_multi

    for ith, i in enumerate(o.context.split(SHAPELY_DIFFERENCE_DESCRIPTION)[1:]):
        i = i.split(NEXT_DIFF_ITEM_INDICATOR)[0].replace("\n", "").strip()
        geom_wkt = i

        sub_operation_id = f"{operation_ith}_{ith}"

        if geom_wkt == "":
            logger.warning(
                f"Empty geometry WKT for operation: {o.operation_type.name} {o.item_type.__name__}, skipping, "
                f"{i}"
            )
            try:
                differences[sub_operation_id] = shapely.wkt.loads(
                    i
                )  # Also one parses a single geom per operation
                if is_multi(differences[sub_operation_id]):
                    rep_points = []
                    for g in differences[sub_operation_id].geoms:
                        rep_points.append(g.representative_point())

                    differences[f"{sub_operation_id}_coherence"] = shapely.LineString(
                        rep_points
                    )
            except:
                logger.error(f"Error parsing geometry WKT: {i=}")

        else:
            try:
                differences[sub_operation_id] = shapely.wkt.loads(
                    geom_wkt
                )  # Also one parses a single geom per operation
                if is_multi(differences[sub_operation_id]):
                    rep_points = []
                    for g in differences[sub_operation_id].geoms:
                        rep_points.append(g.representative_point())

                    differences[f"{sub_operation_id}_coherence"] = shapely.LineString(
                        rep_points
                    )
            except:
                logger.error(f"Error parsing geometry WKT: {geom_wkt=}")

    return differences
