from pynput.mouse import Controller as ConM, Button, Listener as SListM
from pynput.keyboard import Listener as ListK, Key, KeyCode
from Types.DataManager.DataManager import DataManager
from Types.Listerners.Event import EventClick, EventKey, EventKeyRelease, ListEvent, Pos, PosBase
from VARS import database_manager
from Types.app_types import PosParams
from windows.list_monitors import list_monitors
from windows.windows import get_windows_pos

class ListM(SListM):
    def __init__(self, on_click=None, on_move=None, params: PosParams=None):
        self.def_on_click = on_click
        self.params = params

        super().__init__(on_click=self.on_click,
                         on_move=lambda _, __: on_move(*ConM().position))

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

class Listener:
    def __init__(self):
        self.events = ListEvent()

        self.params = None
        self.mouse = None
        self.key = None

    def on_click(self, pos: Pos, button: Button, pressed: bool):
        if pressed:
            self.events.append(EventClick(button.name, pos))

    @staticmethod
    def on_move(x, y):
        pass

    def on_key(self, key: Key | KeyCode):
        if key == Key.esc:
            self.stop()
            return
        if isinstance(key, Key):
            self.events.append(EventKey(f"0{key.name}"))
        if isinstance(key, KeyCode):
            self.events.append(EventKey(f"1{key.vk}"))

    def on_release_key(self, key):
        if isinstance(key, Key):
            self.events.append(EventKeyRelease(f"0{key.name}"))
        if isinstance(key, KeyCode):
            self.events.append(EventKeyRelease(f"1{key.vk}"))

    def start(self, params: PosParams = PosParams(False, "SCREEN", None, (0, 0, 0, ))):
        self.params = params
        self.mouse = ListM(on_click=self.on_click, on_move=self.on_move, params=self.params)
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
        macro_id = data_manager.addMacro(name, categorie)[0]
        for position, event in enumerate(self.events.jsonify()):
            e_type, e_time, data = event
            _position = None
            if e_type == "click":
                _position: Pos = data.pop("pos")
            data = str(data)
            event_id = data_manager.addEvent(e_type, e_time, data, macro_id, (position+1)*1000)[0]
            if _position:
                database_manager.addPosition(*_position.jsonify(), event_id)
        return macro_id

if __name__ == '__main__':

    ls = Listener()

    ls.start()
    ls.join()

    ls.save("Test", "Categ - 1", database_manager)
