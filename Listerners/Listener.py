from pynput.mouse import Controller as ConM, Button, Listener as SListM
from pynput.keyboard import Listener as ListK, Key, KeyCode
import json

from DataManager.DataManager import DataManager
from Listerners.Event import EventClick, EventKey, EventKeyRelease, ListEvent


class ListM(SListM):
    def __init__(self, on_click=None):
        super().__init__(on_click=lambda _, __, btn, pressed: on_click(*ConM().position, btn, pressed))


class Listener:
    def __init__(self):
        self.event = ListEvent()

        self.mouse = ListM(on_click=self.on_click)
        self.key = ListK(on_press=self.on_key, on_release=self.on_release_key)


    def on_click(self, x, y, button: Button, pressed):
        if pressed:
            self.event.append(EventClick(button.name, [x, y]))
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
        self.mouse = ListM(on_click=self.on_click)
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
        for event in self.event.jsonify():
            e_type, e_time, data = event
            data = str(data)
            data_manager.addEvent(e_type, e_time, data, macro_id)
        return macro_id

TABLE_MOUSE = {
    "left": Button.left,
    "right": Button.right,
    "middle": Button.middle,
}

TABLE_KEY = {
    "left": Key.left,
    "right": Key.right,
    "up": Key.up,
    "down": Key.down,
    "space": Key.space
}

if __name__ == '__main__':
    data_manager = DataManager()

    ls = Listener()

    ls.start()
    ls.join()

    ls.save("Test", "Categ - 1", data_manager)
