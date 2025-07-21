#!/usr/bin/python
import logging

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]


def run() -> None: ...
