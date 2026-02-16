import logging

from mi_plugin import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]
FUNCTION_DESCRIPTION = """...
"""
__doc__ = FUNCTION_DESCRIPTION


def run() -> None: ...
