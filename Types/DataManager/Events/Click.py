from Types.Listerners.Pos import Pos
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager


class DatabaseClick:
    def __init__(self, parent: "DataManager"):
        self.parent = parent

    def add(self, time, macro_id, button, position: Pos, order):
        base_event_id = self.parent.Event.add("click", time, macro_id, order)[0]
        position_id = self.parent.Position.add(
            position.base, position.windows_name,
            position.x_pourcent_width, position.x_pourcent_height, position.x_value,
            position.y_pourcent_width, position.y_pourcent_height, position.y_value,
            *position.margins)[0]

        return self.parent.__execute__(f"INSERT INTO event_click (event_id, button, position) VALUES (?, ?, ?)",
                                       (base_event_id, button, position_id))

    def update(self, event_id, time, button, position: Pos, order):
        self.parent.__execute__(f"UPDATE base_event SET time = ?, position = ? WHERE id = ?", (time, order, event_id))
        self.parent.__execute__(f"UPDATE event_click SET button = ? WHERE event_id = ?", (button, event_id))
        position.update(self.parent)

