from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager

class DatabaseWrite:
    def __init__(self, parent: "DataManager"):
        self.parent = parent

    def add(self, time, macro_id, text, order):
        base_event_id = self.parent.Event.add("write", time, macro_id, order)[0]
        return self.parent.__execute__(f"INSERT INTO event_write (event_id, text) VALUES (?, ?)",
                                       (base_event_id, text))

    def update(self, event_id, time, text, order):
        self.parent.__execute__(f"UPDATE base_event SET time = ?, position = ? WHERE id = ?", (time, order, event_id))
        self.parent.__execute__(f"UPDATE event_write SET text = ? WHERE event_id = ?", (text, event_id))
