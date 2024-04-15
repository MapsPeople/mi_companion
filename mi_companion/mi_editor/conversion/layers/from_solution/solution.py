import logging
from typing import Any, Optional, Iterable
from xml.etree.ElementTree import ParseError

import shapely
from jord.qlive_utilities import add_shapely_layer

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject, QgsEditorWidgetSetup

import integration_system
from integration_system.mi import get_remote_solution, SolutionDepth
from integration_system.mi.config import Settings, get_settings
from integration_system.model import Solution
from mi_companion.configuration.constants import (
    MI_HIERARCHY_GROUP_NAME,
    SOLUTION_DESCRIPTOR,
    VENUE_DESCRIPTOR,
    SOLUTION_DATA_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
    NAVIGATION_LINES_DESCRIPTOR,
    GRAPH_DESCRIPTOR,
    NAVIGATION_POINT_DESCRIPTOR,
    ADD_GRAPH,
    MAKE_LOCATION_TYPE_DROPDOWN,
    ALLOW_DUPLICATE_VENUES_IN_PROJECT,
    OSM_HIGHWAY_TYPES,
    MAKE_HIGHWAY_TYPE_DROPDOWN,
    SHOW_GRAPH_ON_LOAD,
    MAKE_DOOR_TYPE_DROPDOWN,
)
from mi_companion.mi_editor.conversion.graph.to_lines import osm_xml_to_lines
from .building import add_building_layers

__all__ = ["solution_venue_to_layer_hierarchy"]


logger = logging.getLogger(__name__)


def solution_venue_to_layer_hierarchy(
    qgis_instance_handle: Any,
    solution_external_id: str,
    venue_external_id: str,
    mi_hierarchy_group_name: str = MI_HIERARCHY_GROUP_NAME,
    *,
    settings: Optional[Settings] = None,
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
    include_occupants: bool = False,
    include_media: bool = False,
    include_route_elements: bool = True,
    include_graph: bool = ADD_GRAPH,
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
    if settings is None:
        settings = get_settings()
    if progress_bar:
        progress_bar.setValue(0)

    layer_tree_root = QgsProject.instance().layerTreeRoot()

    solution = get_remote_solution(
        solution_external_id,
        venue_keys=[venue_external_id],
        settings=settings,
        include_occupants=include_occupants,
        include_media=include_media,
        include_route_elements=include_route_elements,
        include_graph=include_graph,
        depth=depth,
    )

    mi_group = layer_tree_root.findGroup(mi_hierarchy_group_name)

    if not mi_group:  # add it if it does not exist
        mi_group = layer_tree_root.addGroup(mi_hierarchy_group_name)

    mi_group.setExpanded(True)
    # mi_group.setExpanded(False)

    solution_name = f"{solution.name} {SOLUTION_DESCRIPTOR}"
    solution_group = layer_tree_root.findGroup(solution_name)
    if not solution_group:
        solution_group = mi_group.insertGroup(0, solution_name)

    solution_group.setExpanded(True)
    # solution_group.setExpanded(False)

    available_location_type_dropdown_widget = None
    if MAKE_LOCATION_TYPE_DROPDOWN:
        available_location_type_dropdown_widget = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    k: solution.location_types.get(k).name
                    for k in sorted(solution.location_types.keys)
                }
            },
        )

    door_type_dropdown_widget = None
    if MAKE_DOOR_TYPE_DROPDOWN:
        door_type_dropdown_widget = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    f"({integration_system.model.DoorType.__getitem__(k)})": k
                    for k in sorted({l.name for l in integration_system.model.DoorType})
                }
            },
        )

    highway_type_dropdown_widget = None
    if MAKE_HIGHWAY_TYPE_DROPDOWN:
        highway_type_dropdown_widget = (
            QgsEditorWidgetSetup(  # 'UniqueValues', {'Editable':True},
                "ValueMap",
                {"map": {k: OSM_HIGHWAY_TYPES[k] for k in sorted(OSM_HIGHWAY_TYPES)}},
            )
        )

    venue = None
    for v in solution.venues:
        if v.external_id == venue_external_id:
            venue = v
            break

    # solution_layer_name = f"{solution.name}_solution_data"
    # solution_data_layers = QgsProject.instance().mapLayersByName(solution_layer_name)
    # logger.info(f"Found {solution_data_layers}")
    found_solution_data = False
    # found_solution_data = len(solution_data_layers)>0
    for c in solution_group.children():
        if SOLUTION_DATA_DESCRIPTOR in c.name():
            found_solution_data = True

    if not found_solution_data:
        if venue:
            solution_point = venue.polygon.representative_point()
        else:
            solution_point = shapely.Point(0, 0)

        add_shapely_layer(
            qgis_instance_handle=qgis_instance_handle,
            name=SOLUTION_DATA_DESCRIPTOR,
            group=solution_group,
            geoms=[solution_point],  # Does not really matter where this point is
            columns=[
                {
                    "external_id": solution.external_id,
                    "name": solution.name,
                    "customer_id": solution.customer_id,
                    "occupants_enabled": solution.occupants_enabled,
                }
            ],
            visible=False,
        )

    if venue is None:
        logger.warning("Venue was not found!")
        return

    if progress_bar:
        progress_bar.setValue(10)

    venue_name = f"{venue.name} {VENUE_DESCRIPTOR}"

    venue_group = solution_group.findGroup(venue_name)
    if not ALLOW_DUPLICATE_VENUES_IN_PROJECT:  # TODO: base this in external ids instead
        if venue_group:
            logger.error("Venue already loaded!")
            return

    venue_group = solution_group.insertGroup(0, venue_name)
    venue_group.setExpanded(True)
    venue_group.setExpanded(False)

    if ADD_GRAPH:  # add graph
        try:
            if venue.graph and venue.graph.osm_xml:
                (lines, lines_meta_data), (points, points_meta_data) = osm_xml_to_lines(
                    venue.graph.osm_xml
                )

                logger.info(f"{len(lines)=} loaded!")

                graph_name = f"{venue.graph.graph_id} {GRAPH_DESCRIPTOR}"

                graph_group = venue_group.insertGroup(0, graph_name)
                if not SHOW_GRAPH_ON_LOAD:
                    graph_group.setExpanded(True)
                    graph_group.setExpanded(False)
                    graph_group.setItemVisibilityChecked(False)

                graph_lines_layer = add_shapely_layer(
                    qgis_instance_handle=qgis_instance_handle,
                    geoms=lines,
                    name=NAVIGATION_LINES_DESCRIPTOR,
                    group=graph_group,
                    columns=lines_meta_data,
                    categorise_by_attribute="highway",
                    visible=True,
                )

                if highway_type_dropdown_widget:
                    for layers_inner in graph_lines_layer:
                        if layers_inner:
                            if isinstance(layers_inner, Iterable):
                                for layer in layers_inner:
                                    if layer:
                                        layer.setEditorWidgetSetup(
                                            layer.fields().indexFromName("highway"),
                                            highway_type_dropdown_widget,
                                        )
                            else:
                                layers_inner.setEditorWidgetSetup(
                                    layers_inner.fields().indexFromName("highway"),
                                    highway_type_dropdown_widget,
                                )

                if True:  # SHOW POINTs AS WELL
                    logger.info(f"{len(points)=} loaded!")
                    graph_points_layer = add_shapely_layer(
                        qgis_instance_handle=qgis_instance_handle,
                        geoms=points,
                        name=NAVIGATION_POINT_DESCRIPTOR,
                        group=graph_group,
                        columns=points_meta_data,
                        visible=SHOW_GRAPH_ON_LOAD,
                    )
            else:
                logger.warning(f"Venue does not have a valid graph {venue.graph}")

        except ParseError as e:
            logger.error(e)

    add_shapely_layer(
        qgis_instance_handle=qgis_instance_handle,
        geoms=[venue.polygon],
        name=VENUE_POLYGON_DESCRIPTOR,
        columns=[{"external_id": venue.external_id, "name": venue.name}],
        group=venue_group,
        visible=False,
    )

    if progress_bar:
        progress_bar.setValue(20)

    add_building_layers(
        solution=solution,
        progress_bar=progress_bar,
        venue=venue,
        venue_group=venue_group,
        qgis_instance_handle=qgis_instance_handle,
        layer_tree_root=layer_tree_root,
        available_location_type_map_widget=available_location_type_dropdown_widget,
        door_type_dropdown_widget=door_type_dropdown_widget,
    )

    return solution
