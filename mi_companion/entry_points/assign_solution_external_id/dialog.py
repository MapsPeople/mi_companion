import logging
import os

# noinspection PyUnresolvedReferences
from qgis.PyQt import uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QWidget
from typing import Any

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "dialog.ui"))

__all__ = ["Dialog"]

from mi_companion.gui.typing_utilities import get_args, is_optional, is_union

from jord.qgis_utilities.helpers import signals

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)


class Dialog(QDialog, FORM_CLASS):

    def __init__(self, parent: Any = None):
        super().__init__(parent)
        self.setupUi(self)

        signals.reconnect_signal(self.compute_button.clicked, self.on_compute_clicked)

        # import required modules
        import inspect
        from .main import run

        self.parameter_lines = {}
        self.parameter_signature = inspect.signature(run).parameters

        for k, v in reversed(self.parameter_signature.items()):
            label_text = f"{k}"
            default = None
            if v.annotation != v.empty:
                annotation = v.annotation
                label_text += f": {annotation}"
            if v.default != v.empty:
                default = v.default
                label_text += f" = ({default})"

            line_edit = QLineEdit(str(default) if default is not None else None)

            h_box = QHBoxLayout()
            h_box.addWidget(QLabel(label_text))
            h_box.addWidget(line_edit)
            h_box_w = QWidget(self)
            h_box_w.setLayout(h_box)
            self.parameter_layout.insertWidget(0, h_box_w)
            self.parameter_lines[k] = line_edit

        self.parameter_layout.insertWidget(0, QLabel(run.__doc__))

    def on_compute_clicked(self) -> None:
        from .main import run

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

        self.close()
