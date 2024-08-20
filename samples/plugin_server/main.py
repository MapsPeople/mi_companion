import os
import tempfile
from pathlib import Path
from typing import Callable

from flask import Flask, send_from_directory
from google.cloud import storage

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


@app.route("/<string:filename>")
@requires_auth
def get_file(filename: str) -> Response:
    qgis_version = request.args.get("qgis", default="", type=str)  # ?qgis=3.38
    if qgis_version == "3.38" or True:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage.Client.from_service_account_json(
                os.environ.get("SERVICE_ACCOUNT_JSON")
            ).get_bucket("qgisplugins").blob(filename).download_to_filename(
                Path(tmp_dir) / filename
            )
            return send_from_directory(
                directory=tmp_dir, path=filename, as_attachment=False
            )

    return Response("File not found", status=404)


@app.route("/")
def root():
    return app.name


if __name__ == "__main__":
    assert os.environ["SERVICE_ACCOUNT_JSON"]
    assert os.environ["USERNAME"]
    assert os.environ["PASSWORD"]
    app.run(debug=True, port=8000, host="127.0.0.1")
