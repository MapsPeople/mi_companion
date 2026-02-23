import logging
from inspect import isclass
from pathlib import Path

import qgis
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QWidget
from warg import (
    TYPING_TO_BUILTIN_MAP,
    first,
    get_args,
    is_collection_of_strings,
    is_optional,
    is_union,
    parse_collection_string,
)

from .main import FUNCTION_DESCRIPTION

__all__ = ["Dialog"]

from mi_plugin import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)

from jord.qgis_utilities.helpers import signals


class Dialog(QDialog, first(uic.loadUiType(str(Path(__file__).parent / "dialog.ui")))):

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
            # Check if annotation is Path or Optional[Path]
            is_path = False
            if isclass(v.annotation) and issubclass(v.annotation, Path):
                is_path = True
            elif is_optional(v.annotation):
                args = get_args(v.annotation)
                if args and isclass(args[0]) and issubclass(args[0], Path):
                    is_path = True

            if is_path:
                file_browser = qgis.gui.QgsFileWidget()
                file_browser.setFilter("*.csv")
                self.parameter_lines[k] = file_browser

            else:
                self.parameter_lines[k] = QLineEdit(
                    str(default) if default is not None else None
                )

            h_box.addWidget(self.parameter_lines[k])
            h_box_w = QWidget(self)
            h_box_w.setLayout(h_box)
            self.parameter_layout.insertWidget(0, h_box_w)

        self.parameter_layout.insertWidget(0, QLabel(FUNCTION_DESCRIPTION))

    def on_compute_clicked(self) -> None:
        """ """
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
                            # If value is not already of the correct type, try to parse it to the correct type(s) in param_type

                            # ano is a collection of strings like Tuple[str, ...], List[str], Set[str], convert to list of strings
                            if is_collection_of_strings(ano):
                                value = parse_collection_string(value)

                            elif not isinstance(value, param_type):
                                for pt in param_type:
                                    try:
                                        parsed_t = pt(value)
                                        value = parsed_t
                                    except Exception as e:
                                        print(e)
                        else:
                            # If ano is collection of strings like Tuple[str, ...], List[str], Set[str], convert to list of strings
                            if is_collection_of_strings(ano):
                                value = parse_collection_string(value)
                            else:

                                # If ano is not a builtin type but from the typing module, convert to equivalent builtin type, like Tuple to tuple
                                builtin_type = TYPING_TO_BUILTIN_MAP.get(
                                    ano.__name__, ano
                                )
                                value = builtin_type(value)
                    elif (
                        self.parameter_signature[k].default
                        != self.parameter_signature[k].empty
                    ):
                        a = type(self.parameter_signature[k].default)

                        # If a is not a builtin type but from the typing module, convert to equivalent builtin type, like Tuple to tuple
                        builtin_type = TYPING_TO_BUILTIN_MAP.get(a.__name__, a)
                        value = builtin_type(value)
                    call_kwarg[k] = value
            elif isinstance(v, qgis.gui.QgsFileWidget):
                if (
                    not v.filePath()
                    or v.filePath() == "None"
                    or v.filePath().strip() == ""
                ):
                    _logger.error(f"parameter {k} was empty, skipping")
                    continue

                file_path_str = v.splitFilePaths(v.filePath())[
                    0
                ]  # ONLY one supported for now
                if file_path_str:
                    file_path = Path(file_path_str)
                    if file_path.exists() and file_path.is_file():
                        call_kwarg[k] = file_path
                    else:
                        _logger.error(f"{file_path=}")
                else:
                    _logger.error(f"{file_path_str=}")
            else:
                _logger.error(f"{v=}")

        run(**call_kwarg)

        self.close()
