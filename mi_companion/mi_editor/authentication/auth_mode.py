import IPython
import os
import shutil
import sys

from .utilities import _open_new_browser

__all__ = [
    "in_colab_shell",
    "in_jupyter_shell",
    "localhost_is_viable",
    "no_gcloud",
    "GCLOUD_COMMAND",
]

GCLOUD_COMMAND = "gcloud auth application-default login"
DISPLAY_VARIABLES = ["DISPLAY", "WAYLAND_DISPLAY", "MIR_SOCKET"]


def in_colab_shell() -> bool:
    """Tests if the code is being executed within Google Colab."""
    try:
        import google.colab  # pylint: disable=unused-import,redefined-outer-name

        return True
    except ImportError:
        return False


def in_jupyter_shell() -> bool:
    """Tests if the code is being executed within Jupyter."""
    try:
        import ipykernel.zmqshell

        return isinstance(IPython.get_ipython(), ipykernel.zmqshell.ZMQInteractiveShell)
    except ImportError:
        return False
    except NameError:
        return False


def localhost_is_viable() -> bool:
    valid_display = "linux" not in sys.platform or any(
        os.environ.get(var) for var in DISPLAY_VARIABLES
    )
    return valid_display and _open_new_browser("")


def no_gcloud() -> bool:
    return not shutil.which(GCLOUD_COMMAND.split()[0])
