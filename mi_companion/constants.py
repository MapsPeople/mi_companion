import logging
import site  # https://docs.python.org/3/library/site.html#module-site
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def read_version_from_metadata(metadata_file: Path) -> str:
    with open(metadata_file) as f:
        for l in f.readlines():
            if "version=" in l:
                return l.split("=")[-1].strip()
    raise Exception(f"Did not find version in {metadata_file=}")


def read_author_from_metadata(metadata_file: Path) -> str:
    with open(metadata_file) as f:
        for l in f.readlines():
            if "author=" in l:
                return l.split("=")[-1].strip()
    raise Exception(f"Did not find author in {metadata_file=}")


def read_repository_from_metadata(
    metadata_file: Path,
) -> str:  # TODO: GENERALISE TO A single function...
    with open(metadata_file) as f:
        for l in f.readlines():
            if "repository=" in l:
                return l.split("=")[-1].strip()
    raise Exception(f"Did not find repository in {metadata_file=}")


def read_project_name_from_metadata(metadata_file: Path) -> str:
    with open(metadata_file) as f:
        for l in f.readlines():
            if "name=" in l:
                return l.split("=")[-1].strip()
    raise Exception(f"Did not find version in {metadata_file=}")


PLUGIN_DIR = Path(__file__).parent
METADATA_FILE = PLUGIN_DIR / "metadata.txt"

PROJECT_NAME = read_project_name_from_metadata(METADATA_FILE)
VERSION = read_version_from_metadata(METADATA_FILE)
PLUGIN_AUTHOR = read_author_from_metadata(METADATA_FILE)
PLUGIN_REPOSITORY = read_repository_from_metadata(METADATA_FILE)

BUNDLED_PACKAGES_DIR = "mi_companion_bundle"

if not PLUGIN_DIR.is_symlink() or (
    not (Path(__file__).parent.parent / BUNDLED_PACKAGES_DIR).exists()
):
    BUNDLED_PACKAGES_DIR += f".{VERSION}"
    logger.info(
        f"Installed version of plugin detected, targeting {BUNDLED_PACKAGES_DIR}"
    )
else:
    logger.warning(f"Plugin dir is symlinked, assuming development version")

relative_bundled_packages_dir = Path(__file__).parent.parent / BUNDLED_PACKAGES_DIR

if relative_bundled_packages_dir.exists():
    logger.info(f"Loading {relative_bundled_packages_dir}")
    site.addsitedir(str(relative_bundled_packages_dir))
    sys.path = [str(relative_bundled_packages_dir), *sys.path]
else:
    logger.warning(
        f"Could not find bundled packages dir at {relative_bundled_packages_dir}"
    )

try:
    from apppath import AppPath

    PROJECT_APP_PATH = AppPath(PROJECT_NAME, app_author=PLUGIN_AUTHOR)
except Exception:
    PROJECT_APP_PATH = None

__version__ = VERSION
__author__ = PLUGIN_AUTHOR

from jord.qt_utilities import DockWidgetAreaFlag

MANUAL_REQUIREMENTS = [
    "qgis",
    "osgeo",
    # 'qgis' # not visible to pip?
]

RESOURCE_BASE_PATH = "mi_companion"  # PROJECT_NAME.lower().replace(' ', '_')

DEFAULT_PLUGIN_SETTINGS = {
    "RESOURCES_BASE_PATH": f":/{RESOURCE_BASE_PATH}",
    "DEFAULT_WIDGET_AREA": DockWidgetAreaFlag.right,
    "NUM_COLUMNS": 3,
    "MAPS_INDOORS_PASSWORD": "REPLACE_ME",  # TODO: LOOK INTO GOOGLE AUTHENTICATION
    "MAPS_INDOORS_USERNAME": "REPLACE_ME@mapspeople.com",  # TODO: LOOK INTO GOOGLE AUTHENTICATION
    "MAPS_INDOORS_TOKEN_ENDPOINT": "https://auth.mapsindoors.com/connect/token",
    "MAPS_INDOORS_MANAGER_API_HOST": "https://v2.mapsindoors.com",
    "MAPS_INDOORS_MEDIA_API_HOST": "https://media.mapsindoors.com",
    "MAPS_INDOORS_MANAGER_API_TOKEN": None,
    "MAPS_INDOORS_INTEGRATION_API_TOKEN": None,
    "GENERATE_MISSING_EXTERNAL_IDS": True,
    "GENERATE_MISSING_ADMIN_IDS": True,
    "REQUIRE_MINIMUM_FLOOR": True,
    "AWAIT_CONFIRMATION": True,
    "ADVANCED_MODE": False,
    "ADD_GRAPH": True,
    "ADD_ROUTE_ELEMENTS": True,
    "ONLY_SHOW_FIRST_FLOOR": True,
    "CONFIRMATION_DIALOG_ENABLED": True,
    "MAKE_HIGHWAY_TYPE_DROPDOWN": True,
    "MAKE_LOCATION_TYPE_DROPDOWN": True,
    "MAKE_DOOR_TYPE_DROPDOWN": True,
    "MAKE_VENUE_TYPE_DROPDOWN": True,
    "MAKE_CONNECTION_TYPE_DROPDOWN": True,
    "MAKE_EDGE_CONTEXT_TYPE_DROPDOWN": True,
    "MAKE_ENTRY_POINT_TYPE_DROPDOWN": True,
    "GROUPS_FIRST": True,
    "OPERATION_PROGRESS_BAR_ENABLED": True,
    "UPDATE_GRAPH": True,
    "SOLVING_PROGRESS_BAR_ENABLED": True,
    "LOGGING_LEVEL": logging.WARNING,
    "REPROJECT_SHAPES": False,
    "REPROJECT_TO_PROJECT_CRS": True,
    "SHOW_GRAPH_ON_LOAD": False,
    "POST_FIT_FLOORS": False,
    "POST_FIT_BUILDINGS": False,
    "POST_FIT_VENUES": False,
    "ALLOW_SOLUTION_CREATION": False,
    "ALLOW_LOCATION_TYPE_CREATION": False,
    "ALLOW_CATEGORY_TYPE_CREATION": True,
    "IGNORE_EMPTY_SHAPES": True,
    "UPLOAD_OSM_GRAPH": False,
}

MI_EPSG_NUMBER = 4326
GDS_EPSG_NUMBER = 3857

INSERT_INDEX = 0  # if zero first, if one after hierarchy data
USE_EXTERNAL_ID_FLOOR_SELECTION = False
VERBOSE = False
OSM_HIGHWAY_TYPES = {"footway": "footway", "elevator": "elevator", "steps": "steps"}
ALLOW_DUPLICATE_VENUES_IN_PROJECT = False
MAKE_FLOOR_WISE_LAYERS = True
ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES = False
ADD_FLOAT_NAN_CUSTOM_PROPERTY_VALUES = False
ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES = True
DESCRIPTOR_BEFORE = True
DEFAULT_CUSTOM_PROPERTIES = None

HALF_SIZE = 0.5

REAL_NONE_JSON_VALUE = "REAL_NONE"
NAN_VALUE = "nan"
NULL_VALUE = "NULL"
STR_NA_VALUE = "<NA>"
STR_NONE_VALUE = "None"

MI_HIERARCHY_GROUP_NAME = "MapsIndoors (Database)"
SOLUTION_DESCRIPTOR = "(Solution)"
FLOOR_DESCRIPTOR = "(Floor)"
BUILDING_DESCRIPTOR = "(Building)"
VENUE_DESCRIPTOR = "(Venue)"
GRAPH_DESCRIPTOR = "(Graph)"

SOLUTION_DATA_DESCRIPTOR = "solution_data"
FLOOR_POLYGON_DESCRIPTOR = "floor_polygon"
BUILDING_POLYGON_DESCRIPTOR = "building_polygon"
VENUE_POLYGON_DESCRIPTOR = "venue_polygon"
GRAPH_DATA_DESCRIPTOR = "graph_data"
NAVIGATION_HORIZONTAL_LINES_DESCRIPTOR = "horizontal_lines"
NAVIGATION_VERTICAL_LINES_DESCRIPTOR = "vertical_lines"
NAVIGATION_POINT_DESCRIPTOR = "graph_points"

DOORS_DESCRIPTOR = "doors"
CONNECTORS_DESCRIPTOR = "connectors"
AVOIDS_DESCRIPTOR = "avoids"
PREFERS_DESCRIPTOR = "prefers"
BARRIERS_DESCRIPTOR = "barriers"
ENTRY_POINTS_DESCRIPTOR = "entry_points"
OBSTACLES_DESCRIPTOR = "obstacles"

ROUTE_ELEMENT_LAYER_DESCRIPTORS = [
    DOORS_DESCRIPTOR,
    CONNECTORS_DESCRIPTOR,
    AVOIDS_DESCRIPTOR,
    PREFERS_DESCRIPTOR,
    BARRIERS_DESCRIPTOR,
    ENTRY_POINTS_DESCRIPTOR,
    OBSTACLES_DESCRIPTOR,
]

HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS = False
