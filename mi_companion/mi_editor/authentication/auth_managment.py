# noinspection PyUnresolvedReferences
from qgis.core import QgsApplication, QgsAuthManager, QgsAuthMethodConfig

auth_manager = QgsApplication.authManager()

auth_method_id = "MapsIndoorsCredentials"
auth_cfg = QgsAuthMethodConfig()
auth_manager.loadAuthenticationConfig(auth_method_id, auth_cfg, full=True)

credentials = auth_cfg.configMap()

user = credentials["username"]
password = credentials["password"]
