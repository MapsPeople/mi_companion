import logging
import site  # https://docs.python.org/3/library/site.html#module-site
from pathlib import Path

BUNDLED_PACKAGES_DIR = "mi_companion_bundle"

relative_bundled_packages_dir = Path(__file__).parent.parent / BUNDLED_PACKAGES_DIR
logger = logging.getLogger(__name__)

if relative_bundled_packages_dir.exists():
  logger.info(f"Loading {relative_bundled_packages_dir}")
  site.addsitedir(str(relative_bundled_packages_dir))

def read_author_from_metadata(metadata_file: Path) -> str:
  with open(metadata_file) as f:
    for l in f.readlines():
      if "author=" in l:
        return l.split("=")[-1].strip()
  raise Exception(f"Did not find version in {metadata_file=}")

def read_project_name_from_metadata(metadata_file: Path) -> str:
  with open(metadata_file) as f:
    for l in f.readlines():
      if "name=" in l:
        return l.split("=")[-1].strip()
  raise Exception(f"Did not find version in {metadata_file=}")

def read_version_from_metadata(metadata_file: Path) -> str:
  with open(metadata_file) as f:
    for l in f.readlines():
      if "version=" in l:
        return l.split("=")[-1].strip()
  raise Exception(f"Did not find version in {metadata_file=}")

PLUGIN_DIR = Path(__file__).parent
METADATA_FILE = PLUGIN_DIR / "metadata.txt"

PROJECT_NAME = read_project_name_from_metadata(METADATA_FILE)
VERSION = read_version_from_metadata(METADATA_FILE)
PLUGIN_AUTHOR = read_author_from_metadata(METADATA_FILE)

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
DEFAULT_PLUGIN_SETTINGS = {
    "RESOURCES_BASE_PATH": f":/{PROJECT_NAME.lower().replace(' ', '_')}",
    "DEFAULT_WIDGET_AREA": DockWidgetAreaFlag.right,
    "NUM_COLUMNS": 3,
    "MAPS_INDOORS_PASSWORD": "REPLACE_ME",  # TODO: LOOK INTO GOOGLE AUTHENTICATION
    "MAPS_INDOORS_USERNAME": "REPLACE_ME@mapspeople.com",  # TODO: LOOK INTO GOOGLE AUTHENTICATION
    "MAPS_INDOORS_TOKEN_ENDPOINT": "https://auth.mapsindoors.com/connect/token",
    "MAPS_INDOORS_MANAGER_API_HOST": "https://v2.mapsindoors.com",
    "MAPS_INDOORS_MEDIA_API_HOST": "https://media.mapsindoors.com",
    "MAPS_INDOORS_MANAGER_API_TOKEN": None,
    "MAPS_INDOORS_INTEGRATION_API_TOKEN": None,
    "ALLOW_LOCATION_TYPE_CREATION": False,
    "GENERATE_MISSING_EXTERNAL_IDS": True,
    "REQUIRE_MINIMUM_FLOOR": True,
    "ALLOW_SOLUTION_CREATION": False,
    "AWAIT_CONFIRMATION": True,
    "ADVANCED_MODE": False,
    "ADD_GRAPH": True,
    "ADD_DOORS": True,
    "SYNC_GRAPH_AND_ROUTE_ELEMENTS": False,
    "ONLY_SHOW_FIRST_FLOOR": True,
    "CONFIRMATION_DIALOG_ENABLED": True,
    "MAKE_HIGHWAY_TYPE_DROPDOWN": True,
    "MAKE_LOCATION_TYPE_DROPDOWN": True,
    "MAKE_DOOR_TYPE_DROPDOWN": True,
    "MAKE_VENUE_TYPE_DROPDOWN": True,
    "GROUPS_FIRST": True,
    "SHOW_GRAPH_ON_LOAD": False,
    "POST_FIT_FLOORS": False,
    "POST_FIT_BUILDINGS": False,
    "POST_FIT_VENUES": False,
    "OPERATION_PROGRESS_BAR_ENABLED": True,
    "SOLVING_PROGRESS_BAR_ENABLED": True,
    "LOGGING_LEVEL": logging.WARNING,
    "REPROJECT_SHAPES": False,
    }
