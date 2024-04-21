#!/usr/bin/python


def run(*, name: str = "New Building (Building)") -> None:
    import shapely
    from jord.shapely_utilities import dilate
    from mi_companion.mi_editor.conversion import (
        add_building_layers,
    )

    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    from integration_system.model import Solution

    parent = None
    selected_nodes = iface.layerTreeView().selectedNodes()
    if len(selected_nodes) == 1:
        group = next(iter(selected_nodes))
        if isinstance(group, QgsLayerTreeGroup):
            parent = group
        else:
            parent = group.parent()
    else:
        raise ValueError(f"There are {len(selected_nodes)}, please only select one")

    if parent is None:
        raise ValueError(
            f"No parent was found, select one from {iface.layerTreeView()}"
        )

    s = Solution()
    empty_name = "empty"
    empty_polygon = dilate(shapely.Point(0, 0), distance=1e-9)
    venue_key = s.add_venue(empty_name, empty_name, polygon=empty_polygon)
    building_key = s.add_building(
        empty_name, empty_name, polygon=empty_polygon, venue_key=venue_key
    )
    floor_key = s.add_floor(
        empty_name, empty_name, 0, empty_polygon, building_key=building_key
    )
    s.add_room(empty_name, empty_name, polygon=empty_polygon, floor_key=floor_key)
    s.add_area(empty_name, empty_name, polygon=empty_polygon, floor_key=floor_key)
    s.add_point_of_interest(
        empty_name,
        empty_name,
        empty_polygon.representative_point(),
        floor_key=floor_key,
    )

    add_building_layers(
        solution=s,
        # venue=venue,
        # venue_group=venue_group,
        # qgis_instance_handle=qgis_instance_handle,
        # layer_tree_root=layer_tree_root,
        # location_type_drop_down_widget=location_type_down_down_widget,
    )
