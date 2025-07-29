import logging
import os
import subprocess
from pathlib import Path

import pip

from plugin_config import PROFILE, QGIS_APP_PATH
from warg import is_mac, is_windows

logger = logging.getLogger(__name__)

if is_windows():
    qgis_profile_dir = QGIS_APP_PATH.user_config

elif is_mac():
    qgis_profile_dir = QGIS_APP_PATH.user_data  # TOOD: USE CORRECT!

else:
    qgis_profile_dir = QGIS_APP_PATH.user_data


def pip_install_editable(package_paths):
    """Install packages in editable mode.

    Args:
        package_paths: List of package paths to install
    """
    print(f"Installing {len(package_paths)} packages in editable mode...")

    # First uninstall any existing packages
    packages_to_remove = [Path(path).name for path in package_paths]
    if packages_to_remove:
        try:
            subprocess.check_call(
                ["python", "-m", "pip", "uninstall", "-y"] + packages_to_remove
            )
            print(f"Uninstalled: {', '.join(packages_to_remove)}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error uninstalling packages: {e}")

    # Install each package in editable mode
    for path in package_paths:
        try:
            subprocess.check_call(["python", "-m", "pip", "install", "-e", path])
            print(f"Installed: {path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {path}: {e}")
            raise


if __name__ == "__main__":
    for f_n in (
        "mi_companion",
        # f"mi_companion_bundle.{VERSION}"
    ):
        source_folder = (Path(__file__).parent / f_n).absolute()
        target_folder = (
            qgis_profile_dir
            / "profiles"
            / PROFILE
            / "python"
            / "plugins"
            / source_folder.name
        )

        if (
            not target_folder.exists()
        ):  # Does it check for casing of filepath in windows?
            try:
                target_folder.symlink_to(source_folder)
            except OSError as e:
                logger.warning(
                    "Probably missing privileges to make symlink in target parent folder, try running symlinking as "
                    "administrator or change write access('may be read only') / owner."
                )
                raise e
            print("symlinked src->target", source_folder, "->", target_folder)
        else:
            print(target_folder, "already exists!")

    env = os.environ.copy()
    env["SUBMODULE_DIRECTORY"] = str(Path(__file__).parent)
    print(
        subprocess.check_call(
            ["python", "-m", "pip", "install", "-r", "mi_companion/requirements.txt"],
            env=env,
        )
    )
    print(
        subprocess.check_call(
            [
                "python",
                "-m",
                "pip",
                "uninstall",
                "-y",
                "sync_module",
                "midf",
                "svaugely",
                "caddy",
            ]
        )
    )

    # Install packages
    packages = ["./mi_sync", "./midf", "./svaguely", "./caddy"]

    pip_install_editable(packages)
