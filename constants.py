from pathlib import Path

from apppath import AppPath

PROJECT_NAME = "GDS Companion"
PLUGIN_DIR = Path(__file__).parent.parent
VERSION = "0.0.1"
PLUGIN_AUTHOR = "Heider"
PROJECT_APP_PATH = AppPath(PROJECT_NAME, PLUGIN_AUTHOR, VERSION)
DEFAULT_CRS = "EPSG:3857"  # "EPSG:4326"
MANUAL_REQUIREMENTS = [
    "qgis",
    "osgeo"
    # 'qgis' # not visible to pip?
]
__version__ = VERSION
__author__ = PLUGIN_AUTHOR
