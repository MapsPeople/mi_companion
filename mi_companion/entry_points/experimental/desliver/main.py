#!/usr/bin/python
import logging

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = []


def run(*, buffer_size: float = 0.0000016) -> None:
    """

    Desliver polygons

    Buffer size in CRS:
    3857: decimal degrees

    NOT IMPLEMENTED YET!

    :return:
    """

    buffer_size
