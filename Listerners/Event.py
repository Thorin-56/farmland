import datetime
import json

from pynput.keyboard import KeyCode, Key

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

class EventKey(Event):
    def __init__(self, key, time=None, _id=None):
        super().__init__("key", time, _id)
        if key[0] == "1":
            self.key: KeyCode = KeyCode.from_vk(int(key[1:]))
        else:
            assert key[0] == "0"
            self.key: KeyCode = eval(f"Key.{key[1:]}")

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
        return (self.type, self.btn, self.pos_src, self.pos_dst) == (other.type, other.btn, other.pos_src, other.pos_dst)

    def jsonify(self):
        return self.type, self.time, {"btn": self.btn, "pos_src": self.pos_src, "pos_dst": self.pos_dst}

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
        return f"[{self.time}] [{self.type}] Macro: {self.macro}"

    def __eq__(self, other: EventLaunch):
        if type(other) != type(self):
            return False
        return (self.type, self.macro) == (other.type, other.macro)

    def jsonify(self):
        return self.type, self.time, {"macro": self.macro}

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
            e_id, e_type, e_time, macro_id, data, _, _, _ = event
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
        if isinstance(__object, EventKey) and __object.key in self.key_pressed and not isinstance(__object, EventKeyRelease):
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
