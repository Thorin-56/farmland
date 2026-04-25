import datetime

from PySide6.QtCore import QTimer
from pynput.mouse import Button
from pynput.keyboard import KeyCode, Key

from VARS import TABLE_MOUSE, database_manager
from enum import Enum

from windows.list_monitors import list_monitors
from windows.previewOverlay import Window, delete_border, WindowBorder
from windows.windows import get_windows_pos
from PySide6.QtWidgets import QMainWindow

class PosBase(Enum):
    SCREEN = 1
    WINDOWS = 2


class Pos:
    def __init__(self, base=PosBase.SCREEN, windows_name=None, x_value=0, x_pourcent_height=0, x_pourcent_width=0, y_value=0, y_pourcent_height=0,
                 y_pourcent_width=0, margins=(0, 0, 0, 0)):
        self.base: PosBase = base
        assert isinstance(self.base, PosBase) or self.base is None

        self.windows_name = windows_name if self.base is not None else None

        self.x_pourcent_width = x_pourcent_width
        self.x_pourcent_height = x_pourcent_height
        self.x_value = x_value

        self.y_pourcent_width = y_pourcent_width
        self.y_pourcent_height = y_pourcent_height
        self.y_value = y_value

        self.margins = list(margins)

        self.preview: Window | None = None
        self.preview2: WindowBorder | None = None
        self.timer = None
        self.timer2 = None


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

    def affMargins(self):
        x, y, width, height = 0, 0, 0, 0

        if self.base == PosBase.WINDOWS:
            windows_rect = get_windows_pos(self.windows_name)
            if not windows_rect:
                return
            windows_size = (windows_rect[2] - windows_rect[0], windows_rect[3] - windows_rect[1])
            x, y = windows_rect[:2]
            width, height = windows_size

        elif self.base == PosBase.SCREEN:
            monitors_detected = list_monitors()
            monitors_target = list(filter(lambda m: m.get("Device") == self.windows_name, monitors_detected))
            if not monitors_target:
                print(f"Moniteur {self.windows_name} non detecté")
            monitor_rect = monitors_target[0].get("Monitor")
            monitor_size = (monitor_rect[2] - monitor_rect[0], monitor_rect[3] - monitor_rect[1])
            x, y = monitor_rect[:2]
            width, height = monitor_size
        if self.preview2:
            if (self.preview2.x == x and self.preview2.y == y and self.preview2.width == width and self.preview2.height == height and
                    [self.preview2.x_start, self.preview2.x_end, self.preview2.y_start, self.preview2.y_end] == self.margins):
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
        x, y, width, height = 0, 0, 0, 0

        if self.base == PosBase.WINDOWS:
            windows_rect = get_windows_pos(self.windows_name)
            if not windows_rect:
                return
            windows_size = (windows_rect[2] - windows_rect[0], windows_rect[3] - windows_rect[1])
            x, y = windows_rect[:2]
            width, height = windows_size

        elif self.base == PosBase.SCREEN:
            monitors_detected = list_monitors()
            monitors_target = list(filter(lambda m: m.get("Device") == self.windows_name, monitors_detected))
            if not monitors_target:
                print(f"Moniteur {self.windows_name} non detecté")
            monitor_rect = monitors_target[0].get("Monitor")
            monitor_size = (monitor_rect[2] - monitor_rect[0], monitor_rect[3] - monitor_rect[1])
            x, y = monitor_rect[:2]
            width, height = monitor_size

        if self.preview:
            if self.preview.x == x and self.preview.y == y and self.preview.window_size == d:
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
        return f"{self.x_pourcent_width}% + {self.x_value}; {self.y_pourcent_width}% + {self.y_value}"

    def jsonify(self):
        return self.base.name if self.base else None, self.windows_name, self.x_pourcent_width, self.x_pourcent_height, self.x_value, self.y_pourcent_width, self.y_pourcent_height, self.y_value, str(self.margins)

    def __eq__(self, other):
        if isinstance(other, Pos):
            return ((self.base.name if self.base else None, self.windows_name, self.x_pourcent_width, self.x_pourcent_height, self.x_value, self.y_pourcent_width, self.y_pourcent_height, self.y_value, self.margins) ==
                    (other.base.name if other.base else None, other.windows_name, other.x_pourcent_width, other.x_pourcent_height, other.x_value, other.y_pourcent_width, other.y_pourcent_height, other.y_value, other.margins))
        return False

class Event:
    def __init__(self, _type, time=None, _id=None):
        self.id = _id
        self.type = _type
        self.time = time if time is not None else round(datetime.datetime.now().timestamp(), 2)

    def __str__(self):
        return f"[{self.time}] [{self.type}]"

    def __eq__(self, other: Event):
        return self.type == other.type

    def jsonify(self):
        return self.type, self.time, {}

    def isValable(self):
        pass


class EventKey(Event):
    def __init__(self, key, time=None, _id=None):
        super().__init__("key", time, _id)
        if key:
            if key[0] == "1":
                self.key: KeyCode = KeyCode.from_vk(int(key[1:]))
            else:
                assert key[0] == "0"
                self.key: KeyCode = eval(f"Key.{key[1:]}")
        else:
            self.key = None

    def __str__(self):
        return f"[{self.time}] [{self.type}] Key: {self.key if isinstance(self.key, Key) else chr(self.key.vk)}"

    def __eq__(self, other: EventKey):
        if type(other) != type(self):
            return False
        return self.type == other.type and self.key == other.key

    def jsonify(self):
        value = {}
        if isinstance(self.key, Key):
            value["key"] = f"0{self.key.name}"
        else:
            value["key"] = f"1{self.key.vk}"
        return self.type, self.time, value

    def isValable(self):
        return isinstance(self.key, KeyCode) or isinstance(self.key, Key)


class EventKeyRelease(EventKey):
    def __init__(self, key, time=None, _id=None):
        super().__init__(key, time, _id)
        self.type = "key release"


class EventClick(Event):
    def __init__(self, btn, pos, time=None, _id=None):
        super().__init__("click", time, _id)
        self.btn = btn
        self.pos: Pos = pos

    def __str__(self):
        return f"[{self.time}] [{self.type}] Button: {self.btn} Pos: {self.pos}"

    def __eq__(self, other: EventClick):
        if type(other) != type(self):
            return False
        return (self.type, self.btn, self.pos) == (other.type, other.btn, other.pos)

    def jsonify(self):
        return self.type, self.time, {"btn": self.btn, "pos": self.pos}

    def isValable(self):
        return self.btn in TABLE_MOUSE.keys()


class EventMove(Event):
    def __init__(self, btn, pos_src, pos_dst, time=None, _id=None):
        super().__init__("move", time, _id)
        self.btn = btn
        self.pos_src: list[int] = pos_src
        self.pos_dst: list[int] = pos_dst

    def __str__(self):
        return f"[{self.time}] [{self.type}] Button: {self.btn} Pos source: {self.pos_src} Pos destination: {self.pos_dst}"

    def __eq__(self, other: EventMove):
        if type(other) != type(self):
            return False
        return (self.type, self.btn, self.pos_src, self.pos_dst) == (other.type, other.btn, other.pos_src,
                                                                     other.pos_dst)

    def jsonify(self):
        return self.type, self.time, {"btn": self.btn, "pos_src": self.pos_src, "pos_dst": self.pos_dst}

    def isValable(self):
        return (isinstance(self.btn, Button) and
                len(self.pos_src) == 2 and isinstance(self.pos_src[0], int) and isinstance(self.pos_src[1], int) and
                len(self.pos_dst) == 2 and isinstance(self.pos_dst[0], int) and isinstance(self.pos_dst[1], int))


class EventSleep(Event):
    def __init__(self, time=None, _id=None):
        super().__init__("sleep", time, _id)

    def __str__(self):
        return f"[{self.time}] [{self.type}]"

    def __eq__(self, other: EventSleep):
        if type(other) != type(self):
            return False
        return (self.type, self.time) == (other.type, other.time)


class EventLaunch(Event):
    def __init__(self, macro, time=None, _id=None):
        super().__init__("launch", time, _id)
        self.macro = macro

    def __str__(self):
        return f"[{self.time}] [{self.type}] Macro: [{self.macro}] {database_manager.getMacro(self.macro)[1][0][1]}"

    def __eq__(self, other: EventLaunch):
        if type(other) != type(self):
            return False
        return (self.type, self.macro) == (other.type, other.macro)

    def jsonify(self):
        return self.type, self.time, {"macro": self.macro}

    def isValable(self):
        return isinstance(self.macro, int)


class ListEvent(list):
    def __init__(self, events=None):
        super().__init__()
        self.base_time = None
        self.key_pressed = set()

        if events:
            self.__load(events)

    def __load(self, events):
        assert isinstance(events, list)
        final_events = []
        for event in events:
            (e_id, e_type, e_time, macro_id, data, pos_id, base, windows_name,
             x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, event_id, margins) = event
            if e_type == "click":
              margins = eval(margins)
            data = eval(data)
            if base is not None:
                base = PosBase[base]
            match e_type:
                case "key":
                    final_events.append(EventKey(time=e_time, _id=e_id, **data))
                case "key release":
                    final_events.append(EventKeyRelease(time=e_time, _id=e_id, **data))
                case "click":
                    data["pos"] = Pos(base, windows_name, x_value, x_pourcent_height, x_pourcent_width, y_value,
                                      y_pourcent_height, y_pourcent_width, margins)
                    final_events.append(EventClick(time=e_time, _id=e_id, **data))
                case "move":
                    final_events.append(EventMove(time=e_time, _id=e_id, **data))
                case "sleep":
                    final_events.append(EventSleep(time=e_time, _id=e_id))
                case "launch":
                    final_events.append(EventLaunch(time=e_time, _id=e_id, **data))
        for event in final_events:
            super().append(event)

    def append(self, __object: Event):
        if isinstance(__object, EventKey) and __object.key in self.key_pressed and not isinstance(__object,
                                                                                                  EventKeyRelease):
            return

        if not self or __object != self[-1]:
            if not self.base_time:
                self.base_time = __object.time
            _time = __object.time
            __object.time = round(__object.time - self.base_time, 2)
            self.base_time = _time
            super().append(__object)
            if __object.type == "key":
                assert isinstance(__object, EventKey)
                self.key_pressed.add(__object.key)
            if __object.type == "key release":
                assert isinstance(__object, EventKeyRelease)
                self.key_pressed.remove(__object.key)

    def jsonify(self):
        value = [event.jsonify() for event in self]
        return value

    def clear(self):
        super().clear()
        self.base_time = None
