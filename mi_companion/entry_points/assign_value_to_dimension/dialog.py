import logging
import os

# noinspection PyUnresolvedReferences
from qgis.PyQt import uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QWidget

from jord.qgis_utilities.helpers import signals
from mi_companion.gui.typing_utilities import get_args, is_optional, is_union

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "dialog.ui"))

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["Dialog"]


class Dialog(QDialog, FORM_CLASS):

    def __init__(self, parent=None):  #: QWidget

        super().__init__(parent)
        self.setupUi(self)

        signals.reconnect_signal(self.compute_button.clicked, self.on_compute_clicked)

        # import required modules
        import inspect
        from .assign_value_to_geometries import run

        self.parameter_lines = {}
        self.parameter_signature = inspect.signature(run).parameters
        self.ignore_keys = ["iface"]

        for k, v in reversed(self.parameter_signature.items()):
            if k in self.ignore_keys:
                continue
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
            line_edit = QLineEdit(str(default) if default is not None else None)
            h_box.addWidget(line_edit)
            h_box_w = QWidget(self)
            h_box_w.setLayout(h_box)
            self.parameter_layout.insertWidget(0, h_box_w)
            self.parameter_lines[k] = line_edit

        self.parameter_layout.insertWidget(0, QLabel(run.__doc__))

    def on_compute_clicked(self) -> None:
        from .assign_value_to_geometries import run

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
