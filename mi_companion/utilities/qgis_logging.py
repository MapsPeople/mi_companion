import logging
from logging import config
from pathlib import Path

import google.auth.exceptions
import google.cloud
import google.cloud.logging
import yaml

# noinspection PyUnresolvedReferences
from qgis.core import Qgis, QgsMessageLog

__doc__ = "Logging"

__all__ = ["setup_logging"]


def log(msg, level=Qgis.Info):
    QgsMessageLog.logMessage(msg, "MI Companion", level)


def logger_info(msg):
    log(msg)


def logger_warning(msg):
    log(msg, Qgis.Warning)


def logger_error(msg):
    log(msg, Qgis.Critical)


def setup_logging(
    default_path: Path = Path(__file__).parent / "logging.yaml",
    default_level: int = logging.INFO,
) -> None:
    if default_path.exists():
        with open(default_path) as f:
            try:
                config = yaml.safe_load(f.read())

                logging.config.dictConfig(config)

            except ValueError as e:
                print(e)
                print("Error in Logging Configuration. Using default configs")
                logging.basicConfig(level=default_level)

        if True:
            try:
                client = google.cloud.logging.Client()
                client.setup_logging(name="iasjfiasjfisaj")
                print("Sending logs to Google Cloud")
            except google.auth.exceptions.DefaultCredentialsError:
                logging.warning("Could not setup Google Cloud logger", exc_info=True)

    else:
        logging.basicConfig(level=default_level)
        print("Failed to load configuration file. Using default configs")


if __name__ == "__main__":
    setup_logging()
