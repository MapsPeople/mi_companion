import logging
from inspect import isclass
from pathlib import Path

# noinspection PyUnresolvedReferences
import qgis
from jord.qgis_utilities.helpers import signals

# noinspection PyUnresolvedReferences
from qgis.PyQt import uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QWidget

from mi_companion.gui.typing_utilities import get_args, is_optional, is_union

__all__ = ["Dialog"]

FORM_CLASS, _ = uic.loadUiType(str(Path(__file__).parent / "dialog.ui"))

logger = logging.getLogger(__name__)


class Dialog(QDialog, FORM_CLASS):

    def __init__(self, parent=None):  #: QWidget

        super().__init__(parent)
        self.setupUi(self)

        signals.reconnect_signal(self.compute_button.clicked, self.on_compute_clicked)

        # import required modules
        import inspect
        from .main import run

        self.parameter_lines = {}
        self.parameter_signature = inspect.signature(run).parameters
        for k, v in reversed(self.parameter_signature.items()):
            h_box = QHBoxLayout()
            label_text = f"{k}"
            default = None
            if v.annotation != v.empty:
                annotation = v.annotation
                label_text += f": {annotation}"
            if v.default != v.empty:
                default = v.default
                label_text += f" = ({default})"

            h_box.addWidget(QLabel(label_text))
            if isclass(v.annotation) and issubclass(v.annotation, Path):
                file_browser = qgis.gui.QgsFileWidget()

                if default is not None:
                    file_browser.setFilePath(str(default))
                # file_browser.setStorageMode(qgis.gui.QgsFileWidget.StorageMode.GetDirectory)
                # file_browser.fileChanged.connect(self.picked_directory)
                else:
                    file_browser.setFilter("*.dxf")

                self.parameter_lines[k] = file_browser
            else:
                self.parameter_lines[k] = QLineEdit(
                    str(default) if default is not None else None
                )

            h_box.addWidget(self.parameter_lines[k])
            h_box_w = QWidget(self)
            h_box_w.setLayout(h_box)
            self.parameter_layout.insertWidget(0, h_box_w)

        self.parameter_layout.insertWidget(0, QLabel(run.__doc__))

    def on_compute_clicked(self) -> None:
        from .main import run

        call_kwarg = {}
        for k, v in self.parameter_lines.items():
            if isinstance(v, QLineEdit):
                value = v.text()
                if value and value != "None":
                    ano = self.parameter_signature[k].annotation
                    if ano != self.parameter_signature[k].empty:
                        if is_optional(ano) or is_union(ano):
                            param_type = get_args(ano)
                            if not isinstance(value, param_type):
                                for pt in param_type:
                                    try:
                                        parsed_t = pt(value)
                                        value = parsed_t
                                    except Exception as e:
                                        print(e)
                        else:
                            value = ano(value)
                    elif (
                        self.parameter_signature[k].default
                        != self.parameter_signature[k].empty
                    ):
                        value = type(self.parameter_signature[k].default)(value)
                    call_kwarg[k] = value
            elif isinstance(v, qgis.gui.QgsFileWidget):
                file_path_str = v.splitFilePaths(v.filePath())[
                    0
                ]  # ONLY one supported for now
                if file_path_str:
                    file_path = Path(file_path_str)
                    if file_path.exists() and file_path.is_file():
                        call_kwarg[k] = file_path
                    else:
                        logger.error(f"{file_path=}")
                else:
                    logger.error(f"{file_path_str=}")
            else:
                logger.error(f"{v=}")

        run(**call_kwarg)

        self.close()
