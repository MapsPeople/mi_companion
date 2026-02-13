import logging
from qgis.PyQt.QtWidgets import (
    QInputDialog,
    QMessageBox,
)
from qgis.core import QgsApplication, QgsAuthMethodConfig

from jord.qgis_utilities import echo_mode, no_button, yes_button

_logger = logging.getLogger(__name__)


def get_credentials_from_auth_manager(parent=None, auth_cfg_id="mi_login"):
    """
    Retrieves username and password from the QGIS Auth Manager using a
    configuration ID.
    """

    # 1. Attempt to retrieve from QGIS Auth Manager
    if QgsApplication.instance():
        auth_manager = QgsApplication.authManager()

        if auth_manager and auth_cfg_id:
            auth_cfg = QgsAuthMethodConfig()

            # Use loadAuthenticationConfig directly to check validity and load data
            # This avoids 'AttributeError: ... has no attribute authenticationConfig'
            if auth_manager.loadAuthenticationConfig(auth_cfg_id, auth_cfg, full=True):

                # configMap() returns the full dictionary of storage params
                creds = auth_cfg.configMap()
                username = creds.get("username")
                password = creds.get("password")

                if username and password:
                    return username, password

    # 2. Fallback: Prompt the user for credentials
    parent = parent.mainWindow() if parent else None

    dialog_title = "MapsIndoors Authentication"

    # Prompt for Username
    username, ok_user = QInputDialog.getText(
        parent, dialog_title, "MapsIndoors Username/Email (Not Google login!):"
    )

    if not ok_user or not username:
        _logger.error("Invalid Username")
        return None, None

    # Prompt for Password

    password, ok_pass = QInputDialog.getText(
        parent,
        dialog_title,
        "MapsIndoors Password (Reset password on login page if not set yet):",
        echo_mode,
    )

    if not ok_pass or not password:
        _logger.error("Invalid Username")
        return None, None

    # 3. Store the credentials if valid
    if QgsApplication.instance():
        auth_manager = QgsApplication.authManager()
        if auth_manager:
            # Check if we should save this
            reply = QMessageBox.question(
                parent,
                "Save Credentials",
                "Do you want to save these credentials to the QGIS Auth Manager?",
                yes_button | no_button,
                yes_button,
            )

            if reply == yes_button:
                new_conf = QgsAuthMethodConfig()
                new_conf.setId(auth_cfg_id)
                new_conf.setName("MapsIndoors Plugin")
                new_conf.setMethod("Basic")

                # Basic Auth config map
                new_conf.setConfig("username", username)
                new_conf.setConfig("password", password)

                if auth_manager.storeAuthenticationConfig(new_conf):
                    _logger.info(f"Stored authentication config: {auth_cfg_id}")
                else:
                    _logger.error(
                        f"Failed to store authentication config: {auth_cfg_id}"
                    )

    return username, password
