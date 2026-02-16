import logging

from mi_plugin import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]

FUNCTION_DESCRIPTION = """Assigns a coordinate value to all vertices in selected features of any geometry type
"""

__doc__ = FUNCTION_DESCRIPTION


def run() -> None:
    f"""{FUNCTION_DESCRIPTION}

    :return:
    """

    from jord.qlive_utilities import add_no_geom_layer

    columns = [{"a": "b", "c": "d"}, {"a": "c", "c": "d"}, {"a": "c", "c": "e"}]

    add_no_geom_layer(None, columns=columns)
