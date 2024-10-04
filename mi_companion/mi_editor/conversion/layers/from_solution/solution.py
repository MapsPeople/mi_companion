import logging
from typing import Any, Optional

import shapely
from jord.qgis_utilities import read_plugin_setting
from jord.qlive_utilities import add_shapely_layer

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup, QgsProject

import integration_system
from integration_system.mi import (
    SolutionDepth,
    get_remote_solution,
)
from integration_system.model import ConnectionType, Solution, VenueType
from mi_companion import (
    DESCRIPTOR_BEFORE,
    MI_HIERARCHY_GROUP_NAME,
    OSM_HIGHWAY_TYPES,
    SOLUTION_DATA_DESCRIPTOR,
    SOLUTION_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from .venue import add_venue_layer

__all__ = ["solution_venue_to_layer_hierarchy", "add_solution_layers"]

from ...projection import (
    GDS_EPSG_NUMBER,
    should_reproject,
    MI_EPSG_NUMBER,
    prepare_geom_for_qgis,
)

logger = logging.getLogger(__name__)


def add_solution_layers(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    layer_tree_root: Any,
    mi_hierarchy_group_name: str = MI_HIERARCHY_GROUP_NAME,
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
) -> None:
    mi_group = layer_tree_root.findGroup(mi_hierarchy_group_name)

    if not mi_group:  # add it if it does not exist
        mi_group = layer_tree_root.addGroup(mi_hierarchy_group_name)

    mi_group.setExpanded(True)
    # mi_group.setExpanded(False)

    if DESCRIPTOR_BEFORE:
        solution_name = f"{SOLUTION_DESCRIPTOR} {solution.name}"
    else:
        solution_name = f"{solution.name} {SOLUTION_DESCRIPTOR}"

    solution_group = layer_tree_root.findGroup(solution_name)
    if not solution_group:
        solution_group = mi_group.insertGroup(0, solution_name)

    solution_group.setExpanded(True)
    # solution_group.setExpanded(False)

    available_location_type_dropdown_widget = None
    if read_bool_setting("MAKE_LOCATION_TYPE_DROPDOWN"):
        available_location_type_dropdown_widget = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    solution.location_types.get(k).name: k
                    for k in sorted(solution.location_types.keys)
                }
            },
        )

    door_type_dropdown_widget = None
    if read_bool_setting("MAKE_DOOR_TYPE_DROPDOWN"):
        door_type_dropdown_widget = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    name: f"{integration_system.model.DoorType.__getitem__(name)}"
                    for name in sorted(
                        {l.name for l in integration_system.model.DoorType}
                    )
                }
            },
        )

    highway_type_dropdown_widget = None
    if read_plugin_setting("MAKE_HIGHWAY_TYPE_DROPDOWN"):
        highway_type_dropdown_widget = (
            QgsEditorWidgetSetup(  # 'UniqueValues', {'Editable':True},
                "ValueMap",
                {"map": {k: OSM_HIGHWAY_TYPES[k] for k in sorted(OSM_HIGHWAY_TYPES)}},
            )
        )

    venue_type_dropdown_widget = None
    if read_plugin_setting("MAKE_VENUE_TYPE_DROPDOWN"):
        venue_type_dropdown_widget = (
            QgsEditorWidgetSetup(  # 'UniqueValues', {'Editable':True},
                "ValueMap",
                {
                    "map": {
                        name: f"{VenueType.__getitem__(name)}"
                        for name in sorted({l.name for l in VenueType})
                    }
                },
            )
        )

    connection_type_dropdown_widget = None
    if read_plugin_setting("MAKE_CONNECTION_TYPE_DROPDOWN"):
        connection_type_dropdown_widget = (
            QgsEditorWidgetSetup(  # 'UniqueValues', {'Editable':True},
                "ValueMap",
                {
                    "map": {
                        name: f"{ConnectionType.__getitem__(name)}"
                        for name in sorted({l.name for l in ConnectionType})
                    }
                },
            )
        )

    # solution_layer_name = f"{solution.name}_solution_data"
    # solution_data_layers = QgsProject.instance().mapLayersByName(solution_layer_name)
    # logger.info(f"Found {solution_data_layers}")
    found_solution_data = False
    # found_solution_data = len(solution_data_layers)>0
    for c in solution_group.children():
        if SOLUTION_DATA_DESCRIPTOR in c.name():
            found_solution_data = True

    if True:
        assert len(solution.venues) > 0, "No venues found"

    for venue in solution.venues:
        if not found_solution_data:
            if venue:
                solution_point = venue.polygon.representative_point()
            else:
                solution_point = shapely.Point(0, 0)

            layer = add_shapely_layer(
                qgis_instance_handle=qgis_instance_handle,
                name=SOLUTION_DATA_DESCRIPTOR,
                group=solution_group,
                geoms=[
                    prepare_geom_for_qgis(solution_point)
                ],  # Does not really matter where this point is
                columns=[
                    {
                        "external_id": solution.external_id,
                        "name": solution.name,
                        "customer_id": solution.customer_id,
                        "occupants_enabled": solution.occupants_enabled,
                    }
                ],
                visible=False,
                crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER}",
            )

            if False:  # CLEAR GEOMETRY AS IT IS NOT NEEDED, TODO: DOES NOT WORK
                for l in layer:
                    l.startEditing()
                    for f in l.getFeatures():
                        # f:QgsFeature
                        f.clearGeometry()
                        # l.changeGeometry(fid, geom)
                        assert not f.hasGeometry()
                    l.commitChanges()

        if venue is None:
            logger.warning("Venue was not found!")
            return

        if progress_bar:
            progress_bar.setValue(10)

    add_venue_layer(
        progress_bar=progress_bar,
        qgis_instance_handle=qgis_instance_handle,
        solution=solution,
        solution_group=solution_group,
        available_location_type_dropdown_widget=available_location_type_dropdown_widget,
        door_type_dropdown_widget=door_type_dropdown_widget,
        highway_type_dropdown_widget=highway_type_dropdown_widget,
        venue_type_dropdown_widget=venue_type_dropdown_widget,
        connection_type_dropdown_widget=connection_type_dropdown_widget,
    )


def solution_venue_to_layer_hierarchy(
    qgis_instance_handle: Any,
    solution_external_id: str,
    venue_external_id: str,
    mi_hierarchy_group_name: str = MI_HIERARCHY_GROUP_NAME,
    *,
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
    include_occupants: bool = False,
    include_media: bool = False,
    include_route_elements: bool = True,
    include_graph: bool = True,
    depth: SolutionDepth = SolutionDepth.LOCATIONS,
) -> Solution:
    """
    Return solution and created widget objects


    :param include_occupants:
    :param include_media:
    :param include_route_elements:
    :param include_graph:
    :param depth:
    :param qgis_instance_handle:
    :param solution_external_id:
    :param venue_external_id:
    :param mi_hierarchy_group_name:
    :param settings:
    :param progress_bar:
    :return:
    """
    if progress_bar:
        progress_bar.setValue(0)

    layer_tree_root = QgsProject.instance().layerTreeRoot()

    solution = get_remote_solution(
        solution_external_id,
        venue_keys=[venue_external_id],
        include_occupants=include_occupants,
        include_media=include_media,
        include_route_elements=include_route_elements,
        include_graph=include_graph,
        depth=depth,
    )

    add_solution_layers(
        qgis_instance_handle=qgis_instance_handle,
        solution=solution,
        layer_tree_root=layer_tree_root,
        mi_hierarchy_group_name=mi_hierarchy_group_name,
        progress_bar=progress_bar,
    )

    return solution
