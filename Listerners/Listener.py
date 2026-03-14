from pynput.mouse import Controller as ConM, Button, Listener as SListM
from pynput.keyboard import Listener as ListK, Key, KeyCode
import json
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

    def save(self, file_name, path=("list", "test")):
        with open(file_name, "r") as file:
            file = json.load(file)
        current_path: list[dict] = [file]
        for k, i in enumerate(path):
            if k == len(path) - 1:
                current_path.append({i: self.event.jsonify()})
            elif current_path[-1].get(i) is not None:
                current_path.append(current_path[-1].get(i))
            else:
                current_path.append({i: {}})
        value = None
        for k, i in enumerate(current_path[::-1]):
            if value is None:
                value = i[path[-1]]
            else:
                i[path[k*-1]] = value
                value = i
        with open(file_name, 'w') as file:
            json.dump(value, file)

TABLE_MOUSE = {
    "left": Button.left,
    "right": Button.right,
}

TABLE_KEY = {
    "left": Key.left,
    "right": Key.right,
    "up": Key.up,
    "down": Key.down,
    "space": Key.space
}

if __name__ == '__main__':
    ls = Listener()

    ls.start()
    ls.join()

    ls.save("../point.json")

