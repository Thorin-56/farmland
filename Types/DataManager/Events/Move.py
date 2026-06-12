from Types.Listerners.Pos import Pos
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager

class DatabaseMove:
    def __init__(self, parent: "DataManager"):
        self.parent = parent

    def add(self, time, macro_id, position_source: Pos, position_destination: Pos, duration, order):
        base_event_id = self.parent.Event.add("move", time, macro_id, order)[0]
        position_source_id = self.parent.Position.add(
            position_source.base, position_source.windows_name,
            position_source.x_pourcent_width, position_source.x_pourcent_height, position_source.x_value,
            position_source.y_pourcent_width, position_source.y_pourcent_height, position_source.y_value,
            *position_source.margins)[0]
        position_destination_id = self.parent.Position.add(
            position_destination.base, position_destination.windows_name,
            position_destination.x_pourcent_width, position_destination.x_pourcent_height, position_destination.x_value,
            position_destination.y_pourcent_width, position_destination.y_pourcent_height, position_destination.y_value,
            *position_destination.margins)[0]

        return self.parent.__execute__(
            f"INSERT INTO event_move (event_id, position_source, position_destination, duration) "
                  f"VALUES (?, ?, ?, ?)",
            (base_event_id, position_source_id, position_destination_id, duration))

    def update(self, event_id, time, button, duration, pos_src: Pos, pos_dst: Pos, order):
        self.parent.__execute__(f"UPDATE base_event SET time = ?, position = ? WHERE id = ?", (time, order, event_id))
        self.parent.__execute__(f"UPDATE event_move SET button = ?, duration = ? WHERE event_id = ?", (button, duration, event_id))
        pos_src.update(self.parent)
        pos_dst.update(self.parent)
