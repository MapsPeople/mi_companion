#!/usr/bin/python
import logging

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QInputDialog

# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsAuthManager,
    QgsAuthMethodConfig,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)

# noinspection PyUnresolvedReferences
from qgis.utils import iface

__all__ = []

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)


def run(username: str, password: str) -> None:
    """Add an MI layer to the project from available options"""

    auth_manager = QgsApplication.authManager()
    new_auth_cfg = QgsAuthMethodConfig()

    credential_id = "MapsIndoors"

    new_auth_cfg.setId(credential_id)
    new_auth_cfg.setName("MapsIndoors")
    new_auth_cfg.setMethod("APIHeader")
    new_auth_cfg.setUri("https://v2.mapsindoors.com")
    new_auth_cfg.setConfigMap({"username": "test", "password": "test2"})
    auth_manager.storeAuthenticationConfig(new_auth_cfg, overwrite=True)

    auth_cfg = QgsAuthMethodConfig()
    auth_manager.loadAuthenticationConfig(credential_id, auth_cfg, full=True)
    credentials = auth_cfg.configMap()

    user = credentials["username"]
    password = credentials["password"]
    # logger.error(f'{user, password}')
