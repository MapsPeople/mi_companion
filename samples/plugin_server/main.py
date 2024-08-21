import logging
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from flask import Flask, redirect, send_from_directory
from google.cloud import storage

logger = logging.getLogger(__name__)
app = Flask("MapsPeople QGIS Plugin Server")

from functools import wraps
from flask import request, Response


def check_authorization(username: str, password: str) -> bool:
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == os.environ.get("USERNAME") and password == os.environ.get(
        "PASSWORD"
    )


def authenticate() -> Response:
    """Sends a 401 response that enables basic auth"""
    return Response(
        "Could not verify your access level for that URL.\n"
        "You have to login with proper credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )


def requires_auth(f) -> Callable:
    @wraps(f)
    def decorated(*args, **kwargs) -> Response:
        auth = request.authorization

        if not auth or not check_authorization(auth.username, auth.password):
            return authenticate()

        return f(*args, **kwargs)

    return decorated


@app.route("/plugins/<path:path>")
@requires_auth
def get_file(path: str) -> Response:
    qgis_version = request.args.get("qgis", default="", type=str)  # ?qgis=3.38
    if qgis_version == "3.38" or True:
        client = storage.Client.from_service_account_json(
            os.environ.get("SERVICE_ACCOUNT_JSON")
        )
        blob = client.get_bucket("qgisplugins").blob(str(path).replace("%2F", "/"))
        if blob.exists():
            if False:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    last_path_component = Path(blob.path).name
                    target_tmp_path = Path(tmp_dir) / last_path_component

                    blob.download_to_filename(target_tmp_path, raw_download=True)

                    return send_from_directory(
                        directory=tmp_dir, path=last_path_component, as_attachment=False
                    )
            else:
                return redirect(
                    blob.generate_signed_url(datetime.now() + timedelta(hours=1))
                )
        else:
            logger.warning(f"Did not find {blob.path=}")
            return Response(f"Blob {blob.path} not found", status=404)

    return Response(f"File {path} not found", status=404)


@app.route("/")
def root():
    return app.name


if __name__ == "__main__":
    assert os.environ["SERVICE_ACCOUNT_JSON"]
    assert os.environ["USERNAME"]
    assert os.environ["PASSWORD"]
    app.run(debug=True, port=8000, host="127.0.0.1")
