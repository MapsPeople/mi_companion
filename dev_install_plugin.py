import logging
from pathlib import Path

from warg import is_windows, is_mac

from plugin_config import PROFILE, QGIS_APP_PATH

logger = logging.getLogger(__name__)

if is_windows():
    qgis_profile_dir = QGIS_APP_PATH.user_config

elif is_mac():
    qgis_profile_dir = QGIS_APP_PATH.user_data  # TOOD: USE CORRECT!

else:
    qgis_profile_dir = QGIS_APP_PATH.user_data

source_folder = (Path(__file__).parent / "mi_companion").absolute()
target_folder = (
    qgis_profile_dir / "profiles" / PROFILE / "python" / "plugins" / source_folder.stem
)

if __name__ == "__main__":
    if not target_folder.exists():  # Does it check for casing of filepath in windows?
        try:
            target_folder.symlink_to(source_folder)
        except OSError as e:
            logger.warning(
                "Probably missing privileges to make symlink in target parent folder, try running symlinking as administrator or change write access('may be read only') / owner."
            )
            raise e
        print("symlinked src->target", source_folder, "->", target_folder)
    else:
        print(target_folder, "already exists!")
