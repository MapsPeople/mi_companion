import logging
from typing import Tuple

import shapely
from qgis.core import QgsProject, QgsLayerTreeLayer, QgsLayerTreeGroup
from qgis.utils import iface

from mi_plugin import RESOURCE_BASE_PATH
from mi_plugin.layer_descriptors import (
    LOCATION_TYPE_DESCRIPTOR,
    SOLUTION_DATA_DESCRIPTOR,
    SOLUTION_GROUP_DESCRIPTOR,
)
from sync_module.model import (
    Connector,
    FALLBACK_OSM_GRAPH,
    ImplementationStatus,
    SOLUTION_DEFAULT_AVAILABLE_LANGUAGES,
    SOLUTION_DEFAULT_LANGUAGE,
    Solution,
)
from sync_module.shared import (
    LanguageBundle,
    MIConnectionType,
    MIDoorType,
    MIEntryPointType,
    MIMediaType,
    MIOccupantType,
)
from mi_plugin.layer_descriptors import DATABASE_GROUP_DESCRIPTOR
from mi_plugin.mi_editor.conversion import add_solution_layers
from jord.qgis_utilities.helpers import InjectedProgressBar

_logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]

FUNCTION_DESCRIPTION = """Generate an empty hierarchy for map creation from scratch

    Generates a complete MapsIndoors solution hierarchy with buildings, floors, rooms, areas,
    points of interest, and navigation elements for map creation from scratch.


    :param solution_external_id: Unique external identifier for the solution (e.g., "my_mall_solution")
    :type solution_external_id: str
    :param solution_customer_id: Customer/organization ID that owns this solution (e.g., "customer_12345")
    :type solution_customer_id: str
    :param solution_default_language: Default language code for the solution (default: "en")
    :type solution_default_language: str
    :param solution_available_languages: Tuple of all available language codes (default: ("en",))
    :type solution_available_languages: Tuple[str, ...]
    :param number_of_floors: Number of floors to generate in the building (must be positive integer)
    :type number_of_floors: int
"""

__doc__ = FUNCTION_DESCRIPTION


def run(
    *,
    solution_external_id: str,
    solution_customer_id: str,
    # solution_default_language: str = SOLUTION_DEFAULT_LANGUAGE,
    # solution_available_languages: Tuple[        str, ...    ] = SOLUTION_DEFAULT_AVAILABLE_LANGUAGES,
    number_of_floors: int,
) -> None:
    f"""{FUNCTION_DESCRIPTION}

    :return: None (creates QGIS layers and displays in layer tree)
    :rtype: None

    Example::

        # Basic 3-floor solution in English
        run(
            solution_external_id="my_mall",
            solution_customer_id="customer_001",
            number_of_floors=3
        )

        # Multi-language 4-floor solution
        run(
            solution_external_id="intl_mall",
            solution_customer_id="customer_456",
            solution_default_language="en",
            solution_available_languages=("en", "da", "es", "fr"),
            number_of_floors=4
        )
    """

    solution_default_language = SOLUTION_DEFAULT_LANGUAGE
    solution_available_languages = SOLUTION_DEFAULT_AVAILABLE_LANGUAGES

    qgis_instance_handle = QgsProject.instance()
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    mi_solution = Solution(
        solution_external_id,
        solution_external_id,
        _customer_id=solution_customer_id,
        implementation_type=ImplementationStatus.develop,
        occupants_enabled=True,
        _default_language=solution_default_language,
        _available_languages=solution_available_languages,
    )

    dummy_id = "dummy"
    dummy_point = shapely.Point((0, 0))
    dummy_linestring = shapely.LineString(((0, 0), (0, 1)))
    dummy_polygon = dummy_point.buffer(1)
    dummy_translation = {solution_default_language: LanguageBundle(name=dummy_id)}
    graph_key = mi_solution.add_graph(graph_id=dummy_id, osm_xml=FALLBACK_OSM_GRAPH)
    venue_key = mi_solution.add_venue(
        admin_id=dummy_id,
        polygon=dummy_polygon,
        translations=dummy_translation,
        graph_key=graph_key,
    )
    occupant_category_key = mi_solution.add_occupant_category(dummy_id)
    occupant_template_key = mi_solution.add_occupant_template(
        dummy_id,
        occupant_type=MIOccupantType.occupant,
        occupant_category_key=occupant_category_key,
    )
    # location_type_key = mi_solution.add_location_type(        dummy_id, translations=dummy_translation    )
    category_key = mi_solution.add_category(dummy_id, dummy_translation)
    media_key = mi_solution.add_media(dummy_id, data=b"bla", media_type=MIMediaType.png)

    building_key = mi_solution.add_building(
        admin_id=dummy_id,
        polygon=dummy_polygon,
        venue_key=venue_key,
        translations=dummy_translation,
    )
    for f_ith in range(number_of_floors):
        f_key = mi_solution.add_floor(
            f_ith,
            building_key=building_key,
            polygon=dummy_polygon,
            translations=dummy_translation,
        )
        mi_solution.add_room(
            admin_id=f"{dummy_id}{f_ith}",
            polygon=dummy_polygon,
            floor_key=f_key,
            translations=dummy_translation,
        )
        mi_solution.add_area(
            admin_id=f"{dummy_id}{f_ith}",
            polygon=dummy_polygon,
            floor_key=f_key,
            translations=dummy_translation,
        )
        poi_key = mi_solution.add_point_of_interest(
            admin_id=f"{dummy_id}{f_ith}",
            point=dummy_point,
            floor_key=f_key,
            translations=dummy_translation,
        )
        mi_solution.add_occupant(
            location_key=poi_key, occupant_template_key=occupant_template_key
        )
        mi_solution.add_door(
            admin_id=f"{dummy_id}{f_ith}",
            floor_index=f_ith,
            graph_key=graph_key,
            linestring=dummy_linestring,
            door_type=MIDoorType.door,
        )
        mi_solution.add_barrier(
            admin_id=f"{dummy_id}{f_ith}",
            floor_index=f_ith,
            graph_key=graph_key,
            point=dummy_point,
        )
        mi_solution.add_prefer(
            admin_id=f"{dummy_id}{f_ith}",
            floor_index=f_ith,
            graph_key=graph_key,
            point=dummy_point,
        )
        mi_solution.add_avoid(
            admin_id=f"{dummy_id}{f_ith}",
            floor_index=f_ith,
            graph_key=graph_key,
            point=dummy_point,
        )
        mi_solution.add_entry_point(
            admin_id=f"{dummy_id}{f_ith}",
            floor_index=f_ith,
            graph_key=graph_key,
            point=dummy_point,
            entry_point_type=MIEntryPointType.any,
        )
        mi_solution.add_obstacle(
            admin_id=f"{dummy_id}{f_ith}",
            floor_index=f_ith,
            graph_key=graph_key,
            polygon=dummy_point.buffer(0.5),
        )

    mi_solution.add_connection(
        connection_id=0,
        graph_key=graph_key,
        connection_type=MIConnectionType.elevator,
        connectors={
            "0": Connector(
                admin_id=f"{dummy_id}start", floor_index=0, point=dummy_point
            ),
            "1": Connector(admin_id=f"{dummy_id}end", floor_index=1, point=dummy_point),
        },
    )

    with InjectedProgressBar(parent=iface.mainWindow().statusBar()) as progress_bar:
        solution_group = add_solution_layers(
            qgis_instance_handle=qgis_instance_handle,
            solution=mi_solution,
            layer_tree_root=layer_tree_root,
            mi_hierarchy_group_name=DATABASE_GROUP_DESCRIPTOR,
            progress_bar=progress_bar,
        )

    def clear_layer_features(node):
        """Recursively clear features from all layers in a node tree."""
        for child in list(node.children()):
            if isinstance(child, QgsLayerTreeLayer):
                # It's a layer node - delete all features
                if (
                    LOCATION_TYPE_DESCRIPTOR not in child.name()
                    and SOLUTION_DATA_DESCRIPTOR not in child.name()
                ):
                    child.layer().dataProvider().truncate()
            elif isinstance(child, QgsLayerTreeGroup):
                # It's a group node - recurse
                clear_layer_features(child)

    for child in list(solution_group.children()):
        # Clear features from all layers in this node and its children
        clear_layer_features(child)
