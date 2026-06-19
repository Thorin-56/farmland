from Types.Listerners.Pos import Pos
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager


class DatabaseScroll:
    def __init__(self, parent: "DataManager"):
        self.parent = parent

    def add(self, time, macro_id, position: Pos, dx: int, dy: int, order):
        base_event_id = self.parent.Event.add("scroll", time, macro_id, order)[0]
        position_id = self.parent.Position.add(
            position.base, position.windows_name,
            position.x_pourcent_width, position.x_pourcent_height, position.x_value,
            position.y_pourcent_width, position.y_pourcent_height, position.y_value,
            *position.margins)[0]

        return self.parent.__execute__(f"INSERT INTO event_scroll (event_id, position, dx, dy) VALUES (?, ?, ?, ?)",
                                       (base_event_id, position_id, dx, dy))

    def update(self, event_id, time, position: Pos, dx: int, dy: int, order):
        self.parent.__execute__(f"UPDATE base_event SET time = ?, position = ? WHERE id = ?", (time, order, event_id))
        self.parent.__execute__(f"UPDATE event_scroll SET dx = ?, dy = ? WHERE event_id = ?", (dx, dy, event_id))
        position.update(self.parent)

