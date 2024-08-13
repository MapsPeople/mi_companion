import os
from pathlib import Path

from flask import Flask, send_from_directory

app = Flask(__name__)

from functools import wraps
from flask import request, Response


def check_authorization(username: str, password: str) -> bool:
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == os.environ.get("USERNAME") and password == os.environ.get(
        "PASSWORD"
    )


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        "Could not verify your access level for that URL.\n"
        "You have to login with proper credentials",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'},
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
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
        return send_from_directory(
            Path(__file__).parent / "exclude", path=filename, as_attachment=False
        )
    return Response("File not found", status=404)


def explicit():
    from google.cloud import storage

    storage_client = storage.Client.from_service_account_json(
        os.environ.get("SERVICE_ACCOUNT_JSON")
    )

    # Make an authenticated API request
    buckets = list(storage_client.list_buckets())
    print(buckets)


if __name__ == "__main__":
    os.environ["SERVICE_ACCOUNT_JSON"] = ""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""
    os.environ["USERNAME"] = "admin"
    os.environ["PASSWORD"] = "pass"
    app.run(debug=True, port=8000, host="0.0.0.0")
