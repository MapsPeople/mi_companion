import json
import logging
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from qgis.PyQt.QtWidgets import QMessageBox

from mi_companion.mi_editor.authentication import oauth

# fix the warnings/errors messages from 'file_cache is unavailable when using oauth2client'
# https://github.com/googleapis/google-api-python-client/issues/299
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/earthengine",
    "https://www.googleapis.com/auth/devstorage.full_control",
    "https://www.googleapis.com/auth/accounts.reauth",
]

AUTH_HOSTNAME = "localhost"
AUTH_SERVER_PORT = 8085

AUTH_SERVER_ADDR = f"http://{AUTH_HOSTNAME}:{AUTH_SERVER_PORT}/"


class MyAuthenticationHandler(BaseHTTPRequestHandler):
    """
    Listens to localhost:8085 to get the authentication code
    """

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        MyAuthenticationHandler.auth_code = urllib.parse.parse_qs(parsed.query)["code"][
            0
        ]
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(
            bytes(
                f"Authentication for the QGIS {Path(__file__).parent.stem} plugin has been successfully "
                f"completed. "
                "You may now close this page.",
                "utf-8",
            )
        )


def authenticate():
    # show a dialog to allow users to start or cancel the authentication process
    msg = (
        "This plugin uses Google Earth Engine API and it looks like it is not yet\n"
        "authenticated on this machine. You need to have a Google account\n"
        "registered in Google Earth Engine to continue\n\n"
        "Click OK to open a web browser and start the authentication process\n"
        "or click Cancel to stop the authentication process."
    )
    reply = QMessageBox.question(
        None, "Google Earth Engine plugin", msg, QMessageBox.Ok, QMessageBox.Cancel
    )

    if reply == QMessageBox.Cancel:
        return False

    # start the authentication, getting user login & consent
    request_args = {
        "response_type": "code",
        "client_id": oauth.CLIENT_ID,
        "redirect_uri": AUTH_SERVER_ADDR,
        "scope": " ".join(SCOPES),
        "access_type": "offline",
    }
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth/oauthchooseaccount?"
        + urllib.parse.urlencode(request_args)
    )
    webbrowser.open_new(auth_url)
    logger.info("Starting Google Earth Engine Authorization ...")

    server = HTTPServer((AUTH_HOSTNAME, AUTH_SERVER_PORT), MyAuthenticationHandler)
    server.handle_request()

    if not MyAuthenticationHandler.auth_code:
        logger.error(
            "QGIS EE Plugin authentication failed, can not get authentication code"
        )
        return False

    # get refresh token
    request_args = {
        "code": MyAuthenticationHandler.auth_code,
        "client_id": oauth.CLIENT_ID,
        "client_secret": oauth.CLIENT_SECRET,
        "redirect_uri": AUTH_SERVER_ADDR,
        "grant_type": "authorization_code",
    }

    data = urllib.parse.urlencode(request_args).encode()
    response = urllib.request.urlopen(oauth.TOKEN_URI, data).read().decode()
    refresh_token = json.loads(response)["refresh_token"]

    # write refresh token
    oauth.write_private_json(
        oauth.get_credentials_path(),
        {"refresh_token": refresh_token, "scopes": SCOPES},
    )
    logger.info("QGIS EE Plugin authenticated successfully")

    return True


IGNORE_THIS = '''
def import_ee():
    """This is a wrapper of the Google Earth engine library for the
    purpose of initializing or starting ee authentication when the
    user or the plugin import ee library.
    """

    # we can now import the libraries
    # Work around bug https://github.com/google/earthengine-api/issues/181
    import httplib2

    def __wrapping_ee_import__(name, *args, **kwargs):
        _module_ = __builtin_import__(name, *args, **kwargs)
        if name == "ee":
            if not _module_.data._credentials:
                try:
                    _module_.Initialize(http_transport=httplib2.Http())
                except _module_.ee_exception.EEException:
                    if authenticate(ee=_module_):
                        # retry initialization once the user logs in
                        _module_.Initialize(http_transport=httplib2.Http())
                    else:
                        logger.error("\nGoogle Earth Engine authorization failed!\n")

        return _module_

    __builtin_import__ = builtins.__import__
    builtins.__import__ = __wrapping_ee_import__
'''
