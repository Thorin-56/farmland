import datetime

from pynput.mouse import Controller as ConM, Button, Listener as SListM
from pynput.keyboard import Listener as ListK, Key, KeyCode

from typing import Callable

from Types.DataManager.DataManager import DataManager
from Types.Listerners.Event import EventClick, EventKey, EventKeyRelease, ListEvent, Pos, EventMove, EventScroll
from Types.Listerners.Pos import PosBase
from VARS import database_manager
from Types.app_types import PosParams
from windows.list_monitors import list_monitors
from windows.windows import get_windows_pos

class ListM(SListM):
    def __init__(self,
                 on_click: Callable[[Pos, Button, bool], bool | None]=None,
                 on_move=None,
                 on_scroll: Callable[[int, int, int, int], bool | None]=None,
                 params: PosParams=None):
        self.def_on_click = on_click
        self.def_on_scroll = on_scroll
        self.params = params

        super().__init__(on_click=self.on_click,
                         on_move=lambda _, __: on_move(*ConM().position), on_scroll=self.on_scroll)

    def on_click(self, _, __, btn, pressed):
        x, y = ConM().position
        x_pourcent_width = None
        y_pourcent_height = None
        if self.params.is_relative:
            assert isinstance(self.params.base, PosBase)
            if self.params.base == PosBase.WINDOWS:
                windows_rect = get_windows_pos(self.params.base_name)
                windows_size = (windows_rect[2] - windows_rect[0], windows_rect[3] - windows_rect[1])
                x_pourcent_width = (x - windows_rect[0]) /  windows_size[0] * 100
                y_pourcent_height = (y - windows_rect[1]) / windows_size[1] * 100
            elif self.params.base == PosBase.SCREEN:
                monitor_rect = list(filter(lambda m: m.get("Device") == self.params.base_name, list_monitors()))[0].get("Monitor")
                monitor_size = (monitor_rect[2] - monitor_rect[0], monitor_rect[3] - monitor_rect[1])
                x_pourcent_width = (x - monitor_rect[0]) /  monitor_size[0] * 100
                y_pourcent_height = (y - monitor_rect[1]) / monitor_size[1] * 100
            x_pourcent_width, y_pourcent_height = round(x_pourcent_width, 2), round(y_pourcent_height, 2)
            position = Pos(x_value=0, y_value=0,
                           x_pourcent_width=x_pourcent_width, y_pourcent_height=y_pourcent_height,
                           base=self.params.base, windows_name=self.params.base_name)
            return self.def_on_click(position, btn, pressed)

        position = Pos(x_value=x, y_value=y,
                       x_pourcent_width=0, y_pourcent_height=0,
                       base=None, windows_name=None)
        return self.def_on_click(position, btn, pressed)

    def on_scroll(self, _, __, dx, dy):
        x, y = ConM().position
        x_pourcent_width = None
        y_pourcent_height = None
        if self.params.is_relative:
            assert isinstance(self.params.base, PosBase)
            if self.params.base == PosBase.WINDOWS:
                windows_rect = get_windows_pos(self.params.base_name)
                windows_size = (windows_rect[2] - windows_rect[0], windows_rect[3] - windows_rect[1])
                x_pourcent_width = (x - windows_rect[0]) / windows_size[0] * 100
                y_pourcent_height = (y - windows_rect[1]) / windows_size[1] * 100
            elif self.params.base == PosBase.SCREEN:
                monitor_rect = list(filter(lambda m: m.get("Device") == self.params.base_name, list_monitors()))[0].get(
                    "Monitor")
                monitor_size = (monitor_rect[2] - monitor_rect[0], monitor_rect[3] - monitor_rect[1])
                x_pourcent_width = (x - monitor_rect[0]) / monitor_size[0] * 100
                y_pourcent_height = (y - monitor_rect[1]) / monitor_size[1] * 100
            x_pourcent_width, y_pourcent_height = round(x_pourcent_width, 2), round(y_pourcent_height, 2)
            position = Pos(x_value=0, y_value=0,
                           x_pourcent_width=x_pourcent_width, y_pourcent_height=y_pourcent_height,
                           base=self.params.base, windows_name=self.params.base_name)
            return self.def_on_scroll(position, dx, dy)

        position = Pos(x_value=x, y_value=y,
                       x_pourcent_width=0, y_pourcent_height=0,
                       base=None, windows_name=None)
        return self.def_on_scroll(position, dx, dy)

class Listener:
    def __init__(self):
        self.events = ListEvent()

        self.params = None
        self.mouse = None
        self.key = None
        self.pos_mouse_pressed = None
        self.time_mouse_pressed = None

    def on_click(self, pos: Pos, button: Button, pressed: bool):
        if pressed:
            self.time_mouse_pressed = datetime.datetime.now().timestamp()
            self.pos_mouse_pressed = pos
        else:
            if self. pos_mouse_pressed == pos:
                self.events.append(EventClick(button, pos, None))
            else:
                self.events.append(EventMove(button, round(datetime.datetime.now().timestamp() - self.time_mouse_pressed, 2), self.pos_mouse_pressed, pos, None))

    @staticmethod
    def on_move(x, y):
        pass

    def on_key(self, key: Key | KeyCode):
        if key == Key.esc:
            self.stop()
            return
        if isinstance(key, Key):
            self.events.append(EventKey(f"0{key.name}", None))
        if isinstance(key, KeyCode):
            self.events.append(EventKey(f"1{key.vk}", None))

    def on_release_key(self, key):
        if isinstance(key, Key):
            self.events.append(EventKeyRelease(f"0{key.name}", None))
        if isinstance(key, KeyCode):
            self.events.append(EventKeyRelease(f"1{key.vk}", None))

    def on_scroll(self, pos: Pos, dx, dy):
        self.events.append(EventScroll(pos, dx, dy, time=None))

    def start(self, params: PosParams = PosParams(False, "SCREEN", None, (0, 0, 0, ))):
        self.params = params
        self.mouse = ListM(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll, params=self.params)
        self.key = ListK(on_press=self.on_key, on_release=self.on_release_key)
        self.events.clear()
        self.key.start()
        self.mouse.start()

    def stop(self):
        self.mouse.stop()
        self.key.stop()
    def join(self):
        self.key.join()

    def save(self, name, categorie, data_manager: DataManager):
        macro_id = data_manager.Macro.add(name, categorie)[0]
        for position, event in enumerate(self.events):
            event.save(data_manager, macro_id, (position+1)*1000)
        return macro_id

if __name__ == '__main__':

    ls = Listener()

    ls.start()
    ls.join()

    ls.save("Test", "Categ - 1", database_manager)
