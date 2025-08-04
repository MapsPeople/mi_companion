import logging
import subprocess
from pathlib import Path

from dev_install_dependencies import install_dependencies

print(subprocess.check_call(["python3", "-m", "pip", "install",  "apppath", "--break-system-packages"]))


from plugin_config import PROFILE, QGIS_APP_PATH
from warg import ensure_existence, is_mac, is_windows

logger = logging.getLogger(__name__)

if is_windows():
    qgis_profile_dir = QGIS_APP_PATH.user_config

elif is_mac():
    qgis_profile_dir = QGIS_APP_PATH.user_data  # TOOD: USE CORRECT!

else:
    qgis_profile_dir = QGIS_APP_PATH.user_data

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

        ensure_existence(target_folder.parent)

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

    install_dependencies()
