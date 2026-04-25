import time
from VARS import TABLE_MOUSE, TABLE_KEY, database_manager
from Types.Listerners.Event import ListEvent, EventKey, EventKeyRelease, EventClick, EventSleep, EventLaunch, PosBase
from pynput.mouse import Controller as ConM
from pynput.keyboard import Controller as ConK
from windows.list_monitors import list_monitors
from windows.windows import get_windows_pos


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
                    x, y, width, height = 0, 0, 0, 0

                    if event.pos.base == PosBase.WINDOWS:
                        windows_rect = get_windows_pos(event.pos.windows_name)
                        windows_size = (windows_rect[2] - windows_rect[0], windows_rect[3] - windows_rect[1])
                        x, y = windows_rect[:2]
                        width, height = windows_size

                    elif event.pos.base == PosBase.SCREEN:
                        monitors_detected = list_monitors()
                        monitors_target = list(filter(lambda m: m.get("Device") == event.pos.windows_name, monitors_detected))
                        if not monitors_target:
                            print(f"Moniteur {event.pos.windows_name} non detecté")
                            continue
                        monitor_rect = monitors_target[0].get("Monitor")
                        monitor_size = (monitor_rect[2] - monitor_rect[0], monitor_rect[3] - monitor_rect[1])
                        x, y = monitor_rect[:2]
                        width, height = monitor_size

                    ConM().position = event.pos.calcul(x, y, width, height)
                    ConM().click(TABLE_MOUSE[event.btn])
                case "time":
                    assert isinstance(event, EventSleep)
                    pass
                case "launch":
                    assert isinstance(event, EventLaunch)
                    events = database_manager.getEventOfMacro(event.macro)[1]
                    ls = ListEvent(events)
                    Simulator(ls).run()
