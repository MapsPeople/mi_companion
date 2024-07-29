import logging
import typing
from pathlib import Path
from typing import Generic, Union

# noinspection PyUnresolvedReferences
import qgis

# noinspection PyUnresolvedReferences
from qgis.PyQt import uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QWidget

FORM_CLASS, _ = uic.loadUiType(str(Path(__file__).parent / "dialog.ui"))

__all__ = ["Dialog"]


SERIALISED_SOLUTION_EXTENSION = ".json"


try:  # Python >= 3.8
    from typing import Literal, get_args, get_origin

except ImportError:  # Compatibility
    get_args = lambda t: getattr(t, "__args__", ()) if t is not Generic else Generic
    get_origin = lambda t: getattr(t, "__origin__", None)
# assert get_origin(Union[int, str]) is Union
# assert get_args(Union[int, str]) == (int, str)

logger = logging.getLogger(__name__)


def is_union(field) -> bool:
    return typing.get_origin(field) is Union


def is_optional(field) -> bool:
    return is_union(field) and type(None) in typing.get_args(field)


class Dialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):  #: QWidget
        from jord.qgis_utilities.helpers import signals

        super().__init__(parent)
        self.setupUi(self)

        signals.reconnect_signal(self.compute_button.clicked, self.on_compute_clicked)

        # import required modules
        import inspect
        from .main import run

        self.parameter_lines = {}
        self.parameter_signature = inspect.signature(run).parameters
        for k, v in self.parameter_signature.items():
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
            if isinstance(v.annotation, type(Path)):
                file_browser = qgis.gui.QgsFileWidget()
                file_browser.setStorageMode(file_browser.GetFile)
                file_browser.setFilter(f"*{SERIALISED_SOLUTION_EXTENSION}")
                self.parameter_lines[k] = file_browser
            else:
                self.parameter_lines[k] = QLineEdit(str(default))

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
