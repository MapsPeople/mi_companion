import os
import typing
from typing import Generic, Union

from jord.qgis_utilities.helpers import signals

from qgis.PyQt import QtWidgets
from qgis.PyQt import uic
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QLineEdit,
)

from .main import run

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "dialog.ui"))

__all__ = ["InstanceRoomsDialog"]


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


class InstanceRoomsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        signals.reconnect_signal(self.compute_button.clicked, self.on_compute_clicked)

        # import required modules
        import inspect

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
            line_edit = QLineEdit(str(default))
            h_box.addWidget(line_edit)
            h_box_w = QWidget(self)
            h_box_w.setLayout(h_box)
            self.parameter_layout.addWidget(h_box_w)
            self.parameter_lines[k] = line_edit

    def on_compute_clicked(self) -> None:
        call_kwarg = {}
        for k, v in self.parameter_lines.items():
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

        run(**call_kwarg)
