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

MAPS_INDOORS_QGIS_PLUGIN_TITLE = "MapsIndoors QGIS Plugin"

HIERARCHY_VALIDATION_TITLE_BAR = "Hierarchy Validation"
UPLOAD_ERROR_CONFIRMATION_TITLE = "Upload Error"

DEFAULT_PLUGIN_SETTINGS = {
    "RESOURCES_BASE_PATH": f":/{RESOURCE_BASE_PATH}",
    "DEFAULT_WIDGET_AREA": DockWidgetAreaFlag.right,
    "NUM_COLUMNS": 3,
    "MAPS_INDOORS_PASSWORD": "REPLACE_ME",  # TODO: LOOK INTO GOOGLE AUTHENTICATION
    "MAPS_INDOORS_USERNAME": "REPLACE_ME@mapspeople.com",  # TODO: LOOK INTO GOOGLE AUTHENTICATION
    "MAPS_INDOORS_TOKEN_ENDPOINT": "https://auth.mapsindoors.com/connect/token",
    "MAPS_INDOORS_MANAGER_API_HOST": "https://v2.mapsindoors.com",
    "MAPS_INDOORS_MEDIA_API_HOST": "https://media.mapsindoors.com",
    "MAPS_INDOORS_MEDIA_API_TIMEOUT": 1000,
    "MAPS_INDOORS_MANAGER_API_TIMEOUT": 1000,
    "MAPS_INDOORS_MANAGER_API_TOKEN": None,
    "MAPS_INDOORS_INTEGRATION_API_TOKEN": None,
    "GENERATE_MISSING_EXTERNAL_IDS": True,
    "GENERATE_MISSING_ADMIN_IDS": True,
    "REQUIRE_MINIMUM_FLOOR": True,
    "AWAIT_CONFIRMATION": True,
    "ADVANCED_MODE": False,
    "ADD_GRAPH": True,
    "ADD_OCCUPANTS": False,
    "ADD_MEDIA": False,
    "ADD_ROUTE_ELEMENTS": True,
    "ADD_LANGUAGE_BUTTON": False,
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
    "ALLOW_LOCATION_TYPE_CREATION": True,
    "ALLOW_CATEGORY_TYPE_CREATION": True,
    "IGNORE_EMPTY_SHAPES": True,
    "UPLOAD_OSM_GRAPH": False,
    "FLOOR_HEIGHT": 4.0,
    "USE_LOCATION_TYPE_FOR_LABEL": False,
    "LAYER_LABEL_VISIBLE_MIN_RATIO": 1.0 / 999.0,
    "LAYER_GEOM_VISIBLE_MIN_RATIO": 1.0 / 999999.0,
}

INSERT_INDEX = 0  # if zero first, if one after hierarchy data
USE_EXTERNAL_ID_FLOOR_SELECTION = False
VERBOSE = False

ALLOW_DUPLICATE_VENUES_IN_PROJECT = False
MAKE_FLOOR_WISE_LAYERS = True

ADD_STRING_NAN_translation_VALUES = False
ADD_FLOAT_NAN_translation_VALUES = False
ADD_REAL_NONE_translation_VALUES = True

DESCRIPTOR_BEFORE = True
DEFAULT_translations = None
HANDLE_OUTSIDE_FLOORS_SEPARATELY_FROM_BUILDINGS = False
SPLIT_LEVELS_INTO_INDIVIDUAL_GROUPS = False
SHOW_FLOOR_LAYERS_ON_LOAD = True

# NOT FINISHED!
ADD_OCCUPANT_LAYERS = True
ADD_LOCATION_TYPE_LAYERS = True

HALF_SIZE = 0.5

FLOOR_HEIGHT = 4.0
FLOOR_VERTICAL_SPACING = 1.0

GRAPH_EDGE_WIDTH = 1.0
GRAPH_EDGE_COLOR = (255, 0, 0)

DOOR_LINE_WIDTH = 1.0
DOOR_LINE_COLOR = (0, 0, 255)
DOOR_HEIGHT_FACTOR = 0.8

ANCHOR_AS_INDIVIDUAL_FIELDS = True


COMMON_OSM_HIGHWAY_TYPES = {
    "residential": "residential",
    "corridor": "corridor",
    "cycleway": "cycleway",
    "crossing": "crossing",
    "pedestrian": "pedestrian",
    "service": "service",
    "unclassified": "unclassified",
    "tertiary": "tertiary",
    "secondary": "secondary",
    "primary": "primary",
}

OSM_HIGHWAY_TYPES = {
    "footway": "footway",
    "elevator": "elevator",
    "steps": "steps",
    "ladder": "ladder",
}

OSM_ABUTTER_TYPES = {
    "commercial": "commercial",
    "industrial": "industrial",
    "mixed": "mixed",
    "residential": "residential",
    "retail": "retail",
}

if False:
    ...
    # os.environ.setdefault("PYTHONOPTIMIZE", "1")
