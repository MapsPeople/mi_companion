from mi_companion.layer_descriptors import *
from .building_node import *
from .database_node import *
from .floor_components import *
from .graph_components import *
from .location_type_node import *
from .occupant_node import *
from .solution_node import *
from .venue_node import *

__all__ = ["NODE_VALIDATION_MAPPING"]

NODE_VALIDATION_MAPPING = {
    GRAPH_GROUP_DESCRIPTOR: validate_graph_group_node,
    SOLUTION_GROUP_DESCRIPTOR: validate_solution_group_node,
    DATABASE_GROUP_DESCRIPTOR: validate_database_group_node,
    VENUE_GROUP_DESCRIPTOR: validate_venue_group_node,
    BUILDING_GROUP_DESCRIPTOR: validate_building_group_node,
    FLOOR_GROUP_DESCRIPTOR: validate_floor_group_node,
    OCCUPANTS_DESCRIPTOR: validate_occupants_layer_node,
    LOCATION_TYPE_DESCRIPTOR: validate_location_type_layer_node,
    SOLUTION_DATA_DESCRIPTOR: validate_solution_data_layer_node,
    BUILDING_POLYGON_DESCRIPTOR: validate_building_polygon_layer_node,
    VENUE_POLYGON_DESCRIPTOR: validate_venue_polygon_layer_node,
    FLOOR_POLYGON_DESCRIPTOR: validate_floor_polygon_layer_node,
    ROOMS_DESCRIPTOR: validate_rooms_layer_node,
    POINT_OF_INTERESTS_DESCRIPTOR: validate_pois_layer_node,
    AREAS_DESCRIPTOR: validate_areas_layer_node,
    GRAPH_BOUND_DESCRIPTOR: validate_graph_bound_layer_node,
    GRAPH_LINES_DESCRIPTOR: validate_graph_lines_layer_node,
    DOORS_GROUP_DESCRIPTOR: validate_doors_group_node,
    CONNECTORS_GROUP_DESCRIPTOR: validate_connectors_group_node,
    AVOIDS_GROUP_DESCRIPTOR: validate_avoids_group_node,
    PREFERS_GROUP_DESCRIPTOR: validate_prefers_group_node,
    BARRIERS_GROUP_DESCRIPTOR: validate_barriers_group_node,
    ENTRY_POINTS_GROUP_DESCRIPTOR: validate_entry_points_group_node,
    OBSTACLES_GROUP_DESCRIPTOR: validate_obstacles_group_node,
}
