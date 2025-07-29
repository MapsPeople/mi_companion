import os
import subprocess
from pathlib import Path

from dev_install_plugin import logger


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


def install_dependencies():
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


if __name__ == "__main__":
    install_dependencies()
