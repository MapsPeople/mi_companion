import logging
import yaml
from logging import config
from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.core import Qgis, QgsMessageLog

__doc__ = "Logging"

__all__ = ["setup_logging"]

from mi_companion.constants import PROJECT_NAME


def log(msg: str, level=Qgis.Info) -> None:
    """

    :param msg:
    :param level:
    :return:
    """
    QgsMessageLog.logMessage(msg, PROJECT_NAME, level)


def logger_info(msg: str) -> None:
    """

    :param msg:
    :return:
    """
    log(msg)


def logger_warning(msg: str) -> None:
    """

    :param msg:
    :return:
    """
    log(msg, Qgis.Warning)


def logger_error(msg: str) -> None:
    """

    :param msg:
    :return:
    """
    log(msg, Qgis.Critical)


def setup_logging(
    default_path: Path = Path(__file__).parent / "logging.yaml",
    default_level: int = logging.INFO,
) -> None:
    """

    :param default_path:
    :param default_level:
    :return:
    """
    if default_path.exists():
        with open(default_path) as f:
            try:
                config = yaml.safe_load(f.read())

                logging.config.dictConfig(config)

            except ValueError as e:
                print(e)
                print("Error in Logging Configuration. Using default configs")
                logging.basicConfig(level=default_level)

        if False:
            try:
                import google.auth.exceptions
                import google.cloud
                import google.cloud.logging

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
