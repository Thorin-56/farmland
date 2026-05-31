from enum import Enum

from PySide6.QtCore import QTimer

from windows.list_monitors import list_monitors
from windows.previewOverlay import delete_border, Window, WindowBorder
from windows.windows import get_windows_pos


class PosBase(Enum):
    SCREEN = 1
    WINDOWS = 2


class Pos:
    def __init__(self, base=None, windows_name=None, x_value=0, x_pourcent_height=0., x_pourcent_width=0.,
                 y_value=0, y_pourcent_height=0.,
                 y_pourcent_width=0., margins=(0, 0, 0, 0)):
        self.base: PosBase | None = base
        assert isinstance(self.base, PosBase | None)

        self.windows_name = windows_name if self.base is not None else None

        self.x_pourcent_width = float(x_pourcent_width)
        self.x_pourcent_height = float(x_pourcent_height)
        self.x_value = x_value

        self.y_pourcent_width = float(y_pourcent_width)
        self.y_pourcent_height = float(y_pourcent_height)
        self.y_value = y_value

        self.margins = list(margins)

        self.preview: Window | None = None
        self.preview2: WindowBorder | None = None
        self.timer: QTimer | None = None
        self.timer2: QTimer | None = None

    def calcul(self, x, y, width, height):
        position_x = 0
        position_x += (width - self.margins[0] - self.margins[1]) * self.x_pourcent_width / 100
        position_x += (height - self.margins[2] - self.margins[3]) * self.x_pourcent_height / 100

        position_x += self.x_value
        position_x += x + self.margins[0]

        position_y = 0
        position_y += (width - self.margins[0] - self.margins[1]) * self.y_pourcent_width / 100
        position_y += (height - self.margins[2] - self.margins[3]) * self.y_pourcent_height / 100

        position_y += self.y_value
        position_y += y + self.margins[2]

        return position_x, position_y

    def startUpdatePoint(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.updatePoint)
        self.timer.start(10)

    def stopUpdatePoint(self):
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.remove_preview()

    def startUpdateMarges(self):
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.updateMarges)
        self.timer2.start(10)

    def stopUpdateMarges(self):
        if self.timer2:
            self.timer2.stop()
            self.timer2 = None
        self.remove_preview()

    def updateMarges(self):
        self.affMargins()

    def updatePoint(self):
        self.aff_point()

    def base_rect(self):
        if self.base == PosBase.WINDOWS:
            windows_rect = get_windows_pos(self.windows_name)
            if not windows_rect:
                return None
            windows_size = (windows_rect[2] - windows_rect[0], windows_rect[3] - windows_rect[1])
            x, y = windows_rect[:2]
            width, height = windows_size
            return x, y, width, height

        elif self.base == PosBase.SCREEN:
            monitors_detected = list_monitors()
            monitors_target = list(filter(lambda m: m.get("Device") == self.windows_name, monitors_detected))
            if not monitors_target:
                return None
            monitor_rect = monitors_target[0].get("Monitor")
            monitor_size = (monitor_rect[2] - monitor_rect[0], monitor_rect[3] - monitor_rect[1])
            x, y = monitor_rect[:2]
            width, height = monitor_size
            return x, y, width, height
        return 0, 0, 0, 0

    def affMargins(self):
        base_rect = self.base_rect()
        if not base_rect:
            self.timer2.setInterval(2000)
            return
        x, y, width, height = base_rect
        if self.timer2.interval() == 2000:
            self.timer2.setInterval(10)

        if self.preview2:
            if (
                    self.preview2.x == x and self.preview2.y == y and self.preview2.width == width and self.preview2.height == height and
                    [self.preview2.x_start, self.preview2.x_end, self.preview2.y_start,
                     self.preview2.y_end] == self.margins):
                return
            else:
                self.preview2.deleteLater()
                self.preview2 = WindowBorder(x, y, width, height, *self.margins)
                self.preview2.show()
                return
        self.preview2 = WindowBorder(x, y, width, height, *self.margins)
        self.preview2.show()
        delete_border(self.preview2)

    def aff_point(self):
        base_rect = self.base_rect()
        if not base_rect:
            self.timer.setInterval(2000)
            return
        x, y, width, height = base_rect
        if self.timer.interval() == 2000:
            self.timer.setInterval(10)

        if self.preview:
            if self.preview.x == x and self.preview.y == y:
                return
            else:
                self.preview.move(*self.calcul(x, y, width, height))
                return
        self.preview = Window(*self.calcul(x, y, width, height), d=25)
        self.preview.show()
        delete_border(self.preview)

    def remove_preview(self):
        if self.preview:
            self.preview.deleteLater()
            self.preview = None
        if self.preview2:
            self.preview2.deleteLater()
            self.preview2 = None

    def __str__(self):
        if self.base:
            return f"{self.base.name} {self.windows_name} {self.x_pourcent_width}% + {self.x_pourcent_height}%  + {self.x_value}; {self.y_pourcent_width}% + {self.y_pourcent_height}% + {self.y_value}"
        else:
            return f"{self.x_value}; {self.y_value}"

    def jsonify(self):
        return self.base.name if self.windows_name else None, self.windows_name, self.x_pourcent_width, self.x_pourcent_height, self.x_value, self.y_pourcent_width, self.y_pourcent_height, self.y_value, str(
            self.margins)

    def __eq__(self, other):
        if isinstance(other, Pos):
            return ((self.base.name if self.base else None, self.windows_name, self.x_pourcent_width,
                     self.x_pourcent_height, self.x_value, self.y_pourcent_width, self.y_pourcent_height, self.y_value,
                     self.margins) ==
                    (other.base.name if other.base else None, other.windows_name, other.x_pourcent_width,
                     other.x_pourcent_height, other.x_value, other.y_pourcent_width, other.y_pourcent_height,
                     other.y_value, other.margins))
        return False

    def isValable(self):
        return (type(self.x_value) == type(self.y_value) == int and
                type(self.x_pourcent_width) == type(self.x_pourcent_height) == type(self.y_pourcent_width) == type(
                    self.y_pourcent_height) == float and
                type(self.margins) == list and len(self.margins) == 4 and all(
                    [type(marge) == int for marge in self.margins]) and
                (type(self.base) == PosBase or self.base is None) and isinstance(self.windows_name, str | None))