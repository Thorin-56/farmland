from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager

class DatabaseKeyRelease:
    def __init__(self, parent: "DataManager"):
        self.parent = parent

    def add(self, time, macro_id, key, order):
        base_event_id = self.parent.Event.add("key release", time, macro_id, order)[0]
        return self.parent.__execute__(f"INSERT INTO event_key_release (event_id, key) VALUES (?, ?)",
                                       (base_event_id, key))

    def update(self, event_id, time, key, order):
        self.parent.__execute__(f"UPDATE base_event SET time = ?, position = ? WHERE id = ?", (time, order, event_id))
        self.parent.__execute__(f"UPDATE event_key_release SET key = ? WHERE event_id = ?", (key, event_id))