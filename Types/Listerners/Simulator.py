import threading
import time

from pynput.keyboard import Controller as ConK, Listener as LsK, Key, KeyCode
from pynput.mouse import Controller as ConM

from Types.DataManager.DataManager import DataManager
from Types.Listerners.Event import ListEvent, EventKey, EventKeyRelease, EventClick, EventSleep, EventLaunch, \
    EventWrite, EventMove
from VARS import TABLE_KEY


class Simulator:
    def __init__(self, macro_id: int, parent: Simulator=False, macro_index=None):
        self.macro_id = macro_id

        self.database_manager = DataManager()
        events = self.database_manager.Event.getEventOfMacro(self.macro_id)[1]
        self.events = ListEvent(events)

        self._stop = threading.Event()
        self.stop_key = Key.f12

        self.parent = parent
        self.is_sub = not not parent
        self.index = macro_index

        self.start_event = lambda _: None
        self.enter_launch_event = lambda _, __: None

        self.ls = LsK(on_press=self.verifStop) if not parent else None
        self.ConM = ConM()
        self.ConK = ConK()

        self.keys_pressed = set()
        self.sub: Simulator | None = None

    def verifStop(self, key: Key | KeyCode):
        if key == self.stop_key:
            self.stop()

    def run(self):
        if self.ls:
            self.ls.start()
        for k, event in enumerate(self.events):
            self._stop.clear()
            if self.is_sub and self.events.total_time < 0.1:
                pass
            else:
                self.enter_launch_event(self.macro_id, k)
                self.start_event(event.id)
            self._stop.wait(event.time)
            if self._stop.is_set():
                return
            match event.type:
                case "key":
                    assert isinstance(event, EventKey)
                    self.ConK.touch(TABLE_KEY.get(event.key) or event.key, True)
                    self.keys_pressed.add(TABLE_KEY.get(event.key) or event.key)
                case "key release":
                    assert isinstance(event, EventKeyRelease)
                    self.ConK.release(TABLE_KEY.get(event.key) or event.key)
                case "click":
                    assert isinstance(event, EventClick)
                    base_rect = event.pos.base_rect()
                    if not base_rect:
                        return
                    x, y, width, height = base_rect

                    self.ConM.position = event.pos.calcul(x, y, width, height)
                    self.ConM.click(event.btn)
                case "time":
                    assert isinstance(event, EventSleep)
                    pass
                case "launch":
                    assert isinstance(event, EventLaunch)
                    self.sub = Simulator(event.macro, self, k)
                    self.sub.enter_launch_event = self.enter_launch_event
                    self.sub.start_event = self.start_event
                    self.sub._stop = self._stop
                    self.sub.database_manager = self.database_manager
                    self.sub.run()
                    if self._stop.is_set():
                        self.enter_launch_event(self.macro_id, self.index)
                        return
                case "write":
                    assert isinstance(event, EventWrite)
                    self.ConK.type(event.text)
                case "move":
                    assert isinstance(event, EventMove)
                    base_rect = event.pos_src.base_rect()
                    if not base_rect:
                        return
                    x, y, width, height = base_rect

                    pos_src = event.pos_src.calcul(x, y, width, height)
                    self.ConM.position = pos_src
                    time.sleep(0.01)
                    self.ConM.press(event.btn)
                    time.sleep(0.01)
                    base_rect = event.pos_dst.base_rect()
                    if not base_rect:
                        return
                    x, y, width, height = base_rect
                    pos_dst = event.pos_dst.calcul(x, y, width, height)
                    step_numbers = int(max(event.duration, 0.1) // 0.01)
                    vecteur = pos_dst[0] - pos_src[0], pos_dst[1] - pos_src[1]
                    step_vecteur = vecteur[0] / step_numbers, vecteur[1] / step_numbers
                    print(step_vecteur, vecteur, step_numbers)
                    for i in range(step_numbers):
                        self.ConM.position = pos_src[0] + step_vecteur[0] * i, pos_src[1] + step_vecteur[1] * i
                        time.sleep(0.01)
                    self.ConM.position = pos_dst
                    time.sleep(0.01)
                    self.ConM.release(event.btn)
    def stop(self):
        self._stop.set()
        if self.ls:
            self.ls.stop()
        for key in self.keys_pressed:
            self.ConK.release(key)
        if self.sub:
            self.sub.stop()

