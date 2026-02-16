import logging

from mi_plugin import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]
FUNCTION_DESCRIPTION = """Desliver polygons

    Buffer size in CRS:
    3857: decimal degrees

    NOT IMPLEMENTED YET!
"""

__doc__ = FUNCTION_DESCRIPTION


def run(*, buffer_size: float = 0.0000016) -> None:
    f"""{FUNCTION_DESCRIPTION}



    :return:
    """

    buffer_size
