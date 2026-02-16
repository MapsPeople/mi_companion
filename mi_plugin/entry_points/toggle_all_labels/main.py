import logging

from qgis.core import QgsProject, QgsVectorLayer

from mi_plugin import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]
FUNCTION_DESCRIPTION = """Toggle all labels to state

    Either
    On
    or
    Off
"""

__doc__ = FUNCTION_DESCRIPTION


def run(*, state: str = "Off") -> None:
    f"""{FUNCTION_DESCRIPTION}


    :param state:
    :return:
    """
    layers = list(QgsProject.instance().mapLayers().values())

    if isinstance(state, str):
        if state.lower().strip() == "off":
            state = False

    if not isinstance(state, bool):
        state = bool(state)

    if len(layers) == 0:
        _logger.error("No layers found")

    for layer in layers:
        if isinstance(layer, QgsVectorLayer):
            if False:
                _logger.warning(f"Toggle labels for {layer.name()} layer to {state}")
            layer.setLabelsEnabled(state)
            layer.triggerRepaint()
        else:
            _logger.error(f"Did not toggle {layer.name()} label state to {state}")
