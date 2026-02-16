import logging
from pathlib import Path

SHIPPED_PACKAGES_DIR = "packages"

import site  # https://docs.python.org/3/library/site.html#module-site
import platform

platform_postfix = "windows"
if platform.system() == "Darwin":
    platform_postfix = "darwin"
elif platform.system() == "Linux":
    platform_postfix = "linux"

p = Path(__file__).parent.parent / "mi_plugin" / SHIPPED_PACKAGES_DIR / platform_postfix
_logger = logging.getLogger(__name__)

if p.exists():
    _logger.info(f"Loading {p}")
    site.addsitedir(str(p))

if __name__ == "__main__":
    import zmq
    import sync_module

    _logger.info(f"Loading {sync_module.__version__}")

    _logger.error(zmq.zmq_version())
    _logger.error(zmq.backend.zmq_version_info())

    ...
