import logging
from pathlib import Path

from warg import is_mac, is_windows

from mi_companion.constants import VERSION
from plugin_config import PROFILE, QGIS_APP_PATH

logger = logging.getLogger(__name__)

if is_windows():
    qgis_profile_dir = QGIS_APP_PATH.user_config

elif is_mac():
    qgis_profile_dir = QGIS_APP_PATH.user_data  # TOOD: USE CORRECT!

else:
    qgis_profile_dir = QGIS_APP_PATH.user_data

if __name__ == "__main__":
    for f_n in ("mi_companion", f"mi_companion_bundle.{VERSION}"):
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
