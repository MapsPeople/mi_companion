from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.core import QgsApplication

QgsApplication.setPrefixPath(
    str(Path.home() / ".qgis2/"), True
)  # Path to qgis installation
qgs = QgsApplication([], False)
qgs.initQgis()

# Script goes here

qgs.exitQgis()
