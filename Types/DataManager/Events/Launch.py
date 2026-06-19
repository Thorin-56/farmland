from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager

class DatabaseLaunch:
    def __init__(self, parent: "DataManager"):
        self.parent = parent

    def add(self, time, macro_id, macro, order):
        base_event_id = self.parent.Event.add("launch", time, macro_id, order)[0]
        return self.parent.__execute__(f"INSERT INTO event_launch (event_id, macro) VALUES (?, ?)",
                                       (base_event_id, macro))

    def update(self, event_id, time, macro, order):
        self.parent.__execute__(f"UPDATE base_event SET time = ?, position = ? WHERE id = ?", (time, order, event_id))
        self.parent.__execute__(f"UPDATE event_launch SET macro = ? WHERE event_id = ?", (macro, event_id))
