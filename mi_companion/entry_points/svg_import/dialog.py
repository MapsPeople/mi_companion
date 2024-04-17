import typing
from pathlib import Path
from typing import Generic, Union

# noinspection PyUnresolvedReferences
import qgis

# noinspection PyUnresolvedReferences
from qgis.PyQt import uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QDialog

FORM_CLASS, _ = uic.loadUiType(str(Path(__file__).parent / "dialog.ui"))

__all__ = ["SvgImportDialog"]


try:  # Python >= 3.8
    from typing import Literal, get_args, get_origin

except ImportError:  # Compatibility
    get_args = lambda t: getattr(t, "__args__", ()) if t is not Generic else Generic
    get_origin = lambda t: getattr(t, "__origin__", None)
# assert get_origin(Union[int, str]) is Union
# assert get_args(Union[int, str]) == (int, str)


def is_union(field) -> bool:
    return typing.get_origin(field) is Union


def is_optional(field) -> bool:
    return is_union(field) and type(None) in typing.get_args(field)


class SvgImportDialog(QDialog, FORM_CLASS):
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
            if True:
                self.parameter_lines[k] = QLineEdit(str(default))
            else:
                file_browser = qgis.gui.QgsFileWidget()
                file_browser.setFilter(".svg")
                self.parameter_lines[k] = file_browser

            h_box.addWidget(self.parameter_lines[k])
            h_box_w = QWidget(self)
            h_box_w.setLayout(h_box)
            self.parameter_layout.addWidget(h_box_w)

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
                v.filePath  # TODO: FINISH!

        run(**call_kwarg)
