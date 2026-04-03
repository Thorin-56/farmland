import json
import time
from VARS import TABLE_MOUSE, TABLE_KEY, database_manager
from Listerners.Event import ListEvent, EventKey, EventKeyRelease, EventClick, EventSleep, EventLaunch
from pynput.mouse import Controller as ConM
from pynput.keyboard import Controller as ConK
from config import FILE_PATH

class Simulator:
    def __init__(self, events: ListEvent):
        self.events = events

    def run(self):
        for event in self.events:
            time.sleep(event.time)
            match event.type:
                case "key":
                    assert isinstance(event, EventKey)
                    ConK().touch(TABLE_KEY.get(event.key) or event.key, True)
                case "key release":
                    assert isinstance(event, EventKeyRelease)
                    ConK().release(TABLE_KEY.get(event.key) or event.key)
                case "click":
                    assert isinstance(event, EventClick)
                    ConM().position = event.pos
                    ConM().click(TABLE_MOUSE[event.btn])
                case "time":
                    assert isinstance(event, EventSleep)
                    pass
                case "launch":
                    assert isinstance(event, EventLaunch)
                    events = database_manager.getEventOfMacro(event.macro)[1]
                    ls = ListEvent(events)
                    Simulator(ls).run()
