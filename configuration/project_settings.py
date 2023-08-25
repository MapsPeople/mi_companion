from enum import Enum

from PyQt5.QtCore import Qt
from jord.qt_utilities import DockWidgetAreaFlag
from sorcery import assigned_names

from .. import PROJECT_NAME


class ZeroMQProtocol(Enum):
    tcp, udp, pgm, norm, ipc, inproc, gssapi = assigned_names()


DEFAULT_PROJECT_SETTINGS = {
    "RESOURCES_BASE_PATH": f":/{PROJECT_NAME.lower()}",
    "SERVER_PORT": 5555,
    "SERVER_PORT_INCREMENTS": 10,
    "AUTO_START_SERVER": Qt.Checked,
    "SERVER_PROTOCOL": ZeroMQProtocol.tcp,
    "DEFAULT_CLASSIFY_MAPPING": {
        "layer": {
            "A-FURN": {"color": [0, 255, 0]},
            "A-FURN-E": {"color": [0, 150, 0]},
            "A-DOOR-E": {"color": [150, 0, 0]},
            "A-DOOR": {"color": [255, 0, 0]},
            "A-WALL": {"color": [255, 255, 0]},
            "A-WALL-E": {"color": [255, 150, 0]},
            "A-GRID-E": {"color": [0, 0, 255]},
            "triSpaceLayer": {"color": [200, 200, 200]},
        }
    },
    "DEFAULT_WIDGET_AREA": DockWidgetAreaFlag.right,
    "JSON_INDENT": 2,
}
