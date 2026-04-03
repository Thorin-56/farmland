import datetime
from pynput.mouse import Button
from pynput.keyboard import KeyCode, Key

from VARS import TABLE_MOUSE, database_manager
from enum import Enum


class PosBase(Enum):
    SCREEN = 1
    WINDOWS = 2


class Pos:
    def __init__(self, x_value, x_pourcent_height, x_pourcent_width, y_value, y_pourcent_height, y_pourcent_width,
                 windows_name):
        self.base: PosBase = PosBase.SCREEN
        if self.base == PosBase.WINDOWS:
            self.windows_name = windows_name
        else:
            self.windows_name = None

        self.x_pourcent_width = x_pourcent_width
        self.x_pourcent_height = x_pourcent_height
        self.x_value = x_value

        self.y_pourcent_width = y_pourcent_width
        self.y_pourcent_height = y_pourcent_height
        self.y_value = y_value

    def calcul(self, x, y, width, height):
        position_x = 0
        position_x += width * self.x_pourcent_width / 100
        position_x += height * self.x_pourcent_height / 100

        position_x += self.x_value
        position_x += x

        position_y = 0
        position_y += width * self.y_pourcent_width / 100
        position_y += height * self.y_pourcent_height / 100

        position_y += self.y_value
        position_y += y

        return position_x, position_y


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
        self.pos: list[int] = pos

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
            e_id, e_type, e_time, macro_id, data = event
            data = eval(data)
            match e_type:
                case "key":
                    final_events.append(EventKey(time=e_time, _id=e_id, **data))
                case "key release":
                    final_events.append(EventKeyRelease(time=e_time, _id=e_id, **data))
                case "click":
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
