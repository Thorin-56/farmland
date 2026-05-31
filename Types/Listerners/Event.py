import datetime
import json
from abc import abstractmethod, ABC

from pynput.keyboard import KeyCode, Key
from pynput.mouse import Button

from Types.DataManager.DataManager import DataManager
from Types.Listerners.Pos import Pos, PosBase
from VARS import TABLE_MOUSE


class Event(ABC):
    def __init__(self, _type, time=None, _id=None):
        self.id = _id
        self.type = _type
        self.time = time if time is not None else round(datetime.datetime.now().timestamp(), 2)

    def __str__(self):
        return f"[{self.time}] [{self.type}]"

    def __eq__(self, other: Event):
        return (self.type, self.time) == (other.type, other.time)

    @abstractmethod
    def jsonify(self):
        return self.type, self.time, json.dumps({})

    @abstractmethod
    def isValable(self):
        pass


class EventKey(Event):
    def __init__(self, key, time=0., _id=None):
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
        return (self.type, self.time, self.key) == (other.type, other.time, other.key)

    def jsonify(self):
        value = {}
        if isinstance(self.key, Key):
            value["key"] = f"0{self.key.name}"
        elif isinstance(self.key, KeyCode):
            value["key"] = f"1{self.key.vk}"
        else:
            value["key"] = self.key
        return self.type, self.time, json.dumps(value)

    def isValable(self):
        return isinstance(self.key, KeyCode) or isinstance(self.key, Key)


class EventKeyRelease(EventKey):
    def __init__(self, key, time=0., _id=None):
        super().__init__(key, time, _id)
        self.type = "key release"


class EventClick(Event):
    def __init__(self, btn, pos, time=0., _id=None):
        super().__init__("click", time, _id)
        assert isinstance(btn, Button | None)
        self.__btn: Button = btn
        self.pos: Pos = pos

    @property
    def btn(self):
        return self.__btn

    @btn.setter
    def btn(self, value):
        assert isinstance(value, Button | None)
        self.__btn = value

    def __str__(self):
        return f"[{self.time}] [{self.type}] Button: {self.btn.name} Pos: {self.pos}"

    def __eq__(self, other: EventClick):
        if type(other) != type(self):
            return False
        return (self.type, self.time, self.btn, self.pos) == (other.type, other.time, other.btn, other.pos)

    def jsonify(self):
        return self.type, self.time, json.dumps({"btn": self.btn.name if self.btn else None})

    def isValable(self):
        return isinstance(self.btn, Button) and self.pos.isValable()


class EventMove(Event):
    def __init__(self, btn, duration, pos_src, pos_dst, time=None, _id=None):
        super().__init__("move", time, _id)
        self.btn = btn
        self.duration: float = duration
        self.pos_src: Pos = pos_src
        self.pos_dst: Pos = pos_dst

    def __str__(self):
        return f"[{self.time}] [{self.type}] Button: {self.btn} Duration: {self.duration} Pos source: {self.pos_src} Pos destination: {self.pos_dst}"

    def __eq__(self, other: EventMove):
        if type(other) != type(self):
            return False
        return (self.type, self.time, self.btn, self.duration, self.pos_src, self.pos_dst) == (other.type, other.time,
                                                                                               other.btn,
                                                                                               other.duration,
                                                                                               other.pos_src,
                                                                                               other.pos_dst)

    def jsonify(self):
        return self.type, self.time, json.dumps(
            {"btn": self.btn.name if self.btn else None, 'duration': self.duration})

    def isValable(self):
        return (isinstance(self.btn, Button) and
                self.pos_src.isValable() and self.pos_dst.isValable() and
                isinstance(self.duration, float))


class EventSleep(Event):
    def __init__(self, time=None, _id=None):
        super().__init__("sleep", time, _id)

    def __str__(self):
        return f"[{self.time}] [{self.type}]"

    def __eq__(self, other: EventSleep):
        if type(other) != type(self):
            return False
        return (self.type, self.time) == (other.type, other.time)

    def isValable(self):
        return True

    def jsonify(self):
        return self.type, self.time, json.dumps({})


class EventLaunch(Event):
    def __init__(self, macro, time=None, _id=None):
        super().__init__("launch", time, _id)
        self.macro = macro

    def __str__(self):
        return f"[{self.time}] [{self.type}] Macro: [{self.macro}] {DataManager().getMacro(self.macro)[1][1]}"

    def __eq__(self, other: EventLaunch):
        if type(other) != type(self):
            return False
        return (self.type, self.time, self.macro) == (other.type, other.time, other.macro)

    def jsonify(self):
        return self.type, self.time, json.dumps({"macro": self.macro})

    def isValable(self):
        return isinstance(self.macro, int)


class EventWrite(Event):
    def __init__(self, text, time=None, _id=None):
        super().__init__("write", time, _id)
        self.text = text

    def __str__(self):
        return f"[{self.time}] [{self.type}] Text: {self.text}"

    def __eq__(self, other: EventWrite):
        if type(other) != type(self):
            return False
        return (self.type, self.time, self.text) == (other.type, other.time, other.text)

    def jsonify(self):
        return self.type, self.time, json.dumps({"text": self.text})

    def isValable(self):
        return isinstance(self.text, str) and self.text


class ListEvent(list[Event]):
    def __init__(self, events=None):
        super().__init__()
        self.base_time = None
        self.key_pressed = set()
        self.total_time = 0
        if events:
            self.__load(events)

    def __load(self, events):
        assert isinstance(events, list)
        final_events = []
        for event in events:
            event_id, e_type, time, order = event["id"], event["type"], event["time"], event["_order"]

            match e_type:
                case "key":
                    key = event["key_pressed"]
                    final_events.append(EventKey(key, time=time, _id=event_id))
                case "key release":
                    key = event["key_release"]
                    final_events.append(EventKeyRelease(key, time=time, _id=event_id))
                case "click":
                    button, position_id = event["button"], event["position"]
                    position = DataManager().getPosition(position_id)[1]
                    position = Pos(PosBase[position["base"]] if position["base"] else None, position["windows_name"], position["x_value"],
                                   position["x_pourcent_height"], position["x_pourcent_width"], position["y_value"],
                                   position["y_pourcent_height"], position["y_pourcent_width"],
                                   [position["margin_left"], position["margin_right"], position["margin_top"],
                                    position["margin_bottom"]])
                    final_events.append(EventClick(btn=TABLE_MOUSE[button], time=time, _id=event_id, pos=position))
                case "move":
                    position_source_id, position_destination_id, duration = event["position_source"], event[
                        "position_destination"], event["duration"]
                    position = DataManager().getPosition(position_source_id)[1]
                    position_source = Pos(position["base"], position["windows_name"], position["x_value"],
                                   position["x_pourcent_height"], position["x_pourcent_width"], position["y_value"],
                                   position["y_pourcent_height"], position["y_pourcent_width"],
                                   [position["margin_left"], position["margin_right"], position["margin_top"],
                                    position["margin_bottom"]])
                    position = DataManager().getPosition(position_destination_id)[1]
                    position_destination = Pos(position["base"], position["windows_name"], position["x_value"],
                                   position["x_pourcent_height"], position["x_pourcent_width"], position["y_value"],
                                   position["y_pourcent_height"], position["y_pourcent_width"],
                                   [position["margin_left"], position["margin_right"], position["margin_top"],
                                    position["margin_bottom"]])
                    final_events.append(
                        EventMove(TABLE_MOUSE["left"], duration, position_source, position_destination, time=time,
                                  _id=event_id))
                case "sleep":
                    final_events.append(EventSleep(time=time, _id=event_id))
                case "launch":
                    macro = event["macro"]
                    final_events.append(EventLaunch(macro, time, event_id))
                case "write":
                    text = event["text"]
                    final_events.append(EventWrite(text, time, event_id))
        for event in final_events:
            self.total_time += event.time
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
            self.total_time += __object.time
            super().append(__object)
            if __object.type == "key":
                assert isinstance(__object, EventKey)
                self.key_pressed.add(__object.key)
            if __object.type == "key release":
                assert isinstance(__object, EventKeyRelease)
                self.key_pressed.remove(__object.key)

    def jsonify(self):
        return [event.jsonify() for event in self]

    def clear(self):
        super().clear()
        self.base_time = None
        self.total_time = 0

    def remove(self, __value):
        if isinstance(__value, Event):
            self.total_time -= __value.time
        super().remove(__value)
