# noinspection PyUnresolvedReferences
from typing import Any

from qgis.PyQt.QtWidgets import QMessageBox, QTextEdit


class ResizableMessageBox(QMessageBox):  # TODO: MOVE THIS TO JORD!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizeGripEnabled(True)

    def event(self, event: Any) -> Any:
        if event.type() in (event.LayoutRequest, event.Resize):
            if event.type() == event.Resize:
                res = super().event(event)
            else:
                res = False

            details = self.findChild(QTextEdit)

            if details:
                details.setMaximumSize(16777215, 16777215)

            self.setMaximumSize(16777215, 16777215)
            return res

        return super().event(event)
