import datetime
from pynput.keyboard import KeyCode, Key

class Event:
    def __init__(self, _type, time=None):
        self.type = _type
        self.time = time if time is not None else round(datetime.datetime.now().timestamp(), 2)

    def __str__(self):
        return f"[{self.time}] [{self.type}]"

    def __eq__(self, other: Event):
        return self.type == other.type

class EventKey(Event):
    def __init__(self, key, time=None):
        super().__init__("key", time)
        if key[0] == "1":
            self.key: KeyCode = KeyCode.from_vk(int(key[1:]))
        else:
            assert key[0] == "0"
            self.key: KeyCode = eval(f"Key.{key[1:]}")

    def __str__(self):
        return f"[{self.time}] [{self.type}] Key: {self.key}"

    def __eq__(self, other: EventKey):
        if type(other) != type(self):
            return False
        return self.type == other.type and self.key == other.key

    def jsonify(self):
        value = {"type": self.type, "time": self.time}
        if isinstance(self.key, Key):
            value["key"] = f"0{self.key.name}"
        else:
            value["key"] = f"1{self.key.vk}"
        return value

class EventKeyRelease(Event):
    def __init__(self, key, time=None):
        super().__init__("key release", time)
        if key[0] == "1":
            self.key = KeyCode.from_vk(int(key[1:]))
        else:
            assert key[0] == "0"
            self.key: Key | KeyCode = eval(f"Key.{key[1:]}")

    def __str__(self):
        return f"[{self.time}] [{self.type}] Key: {self.key}"

    def __eq__(self, other: EventKeyRelease):
        if type(other) != type(self):
            return False
        return self.type == other.type and self.key == other.key

    def jsonify(self):
        value = {"type": self.type, "time": self.time}
        if isinstance(self.key, Key):
            value["key"] = f"0{self.key.name}"
        else:
            value["key"] = f"1{self.key.vk}"
        return value

class EventClick(Event):
    def __init__(self, btn, pos, time=None):
        super().__init__("click", time)
        self.btn = btn
        self.pos = pos

    def __str__(self):
        return f"[{self.time}] [{self.type}] Button: {self.btn} Pos: {self.pos}"

    def __eq__(self, other: EventClick):
        if type(other) != type(self):
            return False
        return (self.type, self.btn, self.pos) == (other.type, other.btn, other.pos)

    def jsonify(self):
        return {"type": self.type, "time": self.time, "btn": self.btn, "pos": self.pos}

class EventSleep(Event):
    def __init__(self, time=None):
        super().__init__("sleep", time)

    def __str__(self):
        return f"[{self.time}] [{self.type}]"

    def __eq__(self, other: EventSleep):
        if type(other) != type(self):
            return False
        return (self.type, self.time) == (other.type, other.time)

    def jsonify(self):
        return {"type": self.type, "time": self.time}

class EventLaunch(Event):
    def __init__(self, categ, name, time=None):
        super().__init__("launch", time)
        self.categ = categ
        self.name = name

    def __str__(self):
        return f"[{self.time}] [{self.type}] Categ: {self.categ} Name: {self.name}"

    def __eq__(self, other: EventLaunch):
        if type(other) != type(self):
            return False
        return (self.type, self.categ, self.name) == (other.type, other.categ, other.name)

    def jsonify(self):
        return {"type": self.type, "time": self.time, "categ": self.categ, "name": self.name}

class ListEvent(list):
    def __init__(self, json_events=None):
        super().__init__()
        self.base_time = None
        self.key_pressed = set()

        if json_events:
            self.__load(json_events)

    def __load(self, json_events):
        assert isinstance(json_events, list)
        events = []
        for event in json_events:
            assert isinstance(event, dict)
            match event.get("type"):
                case "key":
                    events.append(EventKey(event.get("key"), event.get("time")))
                case "key release":
                    events.append(EventKeyRelease(event.get("key"), event.get("time")))
                case "click":
                    events.append(EventClick(event.get("btn"), event.get("pos"), event.get("time")))
                case "sleep":
                    events.append(EventSleep(event.get("time")))
                case "launch":
                    events.append(EventLaunch(event.get("categ"), event.get("name"), event.get("time")))
        for event in events:
            super().append(event)

    def append(self, __object: Event):
        if isinstance(__object, EventKey) and __object.key in self.key_pressed:
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
