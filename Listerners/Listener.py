from pynput.mouse import Controller as ConM, Button, Listener as SListM
from pynput.keyboard import Listener as ListK, Key, KeyCode
from DataManager.DataManager import DataManager
from Listerners.Event import EventClick, EventKey, EventKeyRelease, ListEvent, Pos
from VARS import database_manager

class ListM(SListM):
    def __init__(self, on_click=None, on_move=None):
        super().__init__(on_click=lambda _, __, btn, pressed: on_click(*ConM().position, btn, pressed),
                         on_move=lambda _, __: on_move(*ConM().position))


class Listener:
    def __init__(self):
        self.event = ListEvent()

        self.mouse = ListM(on_click=self.on_click, on_move=self.on_move)
        self.key = ListK(on_press=self.on_key, on_release=self.on_release_key)

    def on_click(self, x, y, button: Button, pressed):
        if pressed:
            self.event.append(EventClick(button.name, Pos(x_value=x, y_value=y)))

    def on_move(self, x, y):
        print(x, y)

    def on_key(self, key: Key | KeyCode):
        if key == Key.esc:
            self.stop()
            return
        if isinstance(key, Key):
            self.event.append(EventKey(f"0{key.name}"))
        if isinstance(key, KeyCode):
            self.event.append(EventKey(f"1{key.vk}"))

    def on_release_key(self, key):
        if isinstance(key, Key):
            self.event.append(EventKeyRelease(f"0{key.name}"))
        if isinstance(key, KeyCode):
            self.event.append(EventKeyRelease(f"1{key.vk}"))

    def start(self):
        self.mouse = ListM(on_click=self.on_click, on_move=self.on_move)
        self.key = ListK(on_press=self.on_key, on_release=self.on_release_key)
        self.event.clear()
        self.key.start()
        self.mouse.start()

    def stop(self):
        self.mouse.stop()
        self.key.stop()
    def join(self):
        self.key.join()

    def save(self, name, categorie, data_manager: DataManager):
        macro_id = data_manager.addMacro(name, categorie)[0]
        for position, event in enumerate(self.event.jsonify()):
            e_type, e_time, data = event
            _position = None
            if e_type == "click":
                _position: Pos = data.pop("pos")
            data = str(data)
            event_id = data_manager.addEvent(e_type, e_time, data, macro_id, position+1)[0]
            if _position:
                database_manager.addPosition(*_position.jsonify(), event_id)
        return macro_id

if __name__ == '__main__':

    ls = Listener()

    ls.start()
    ls.join()

    ls.save("Test", "Categ - 1", database_manager)
