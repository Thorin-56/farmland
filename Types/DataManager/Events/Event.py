from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager

class DatabaseEvent:
    def __init__(self, parent: "DataManager"):
        self.parent = parent

    def add(self, e_type, time, macro_id, position) -> tuple[int]:
        return self.parent.__execute__(f"INSERT INTO base_event (type, time, macro_id, position) VALUES (?, ?, ?, ?)",
                                (e_type, time, macro_id, position))

    def delete(self, event_id) -> tuple[int]:
        return self.parent.__execute__("DELETE FROM base_event WHERE id = ?", (event_id,))
    
    def getEventOfMacro(self, macro_id, start=0, end=-1) -> tuple[int, list]:
        return self.parent.__execute__(
            f"SELECT base_event.id, type, time, base_event.position as _order, macro_id, "
            f"ec.button, ec.position, "
            f"el.macro, " 
            f"em.position_source, em.position_destination, em.duration, "
            f"ew.text, "
            f"ekp.key as key_pressed, "
            f"ekr.key as key_release FROM base_event "
            f"LEFT JOIN main.event_move em on base_event.id = em.event_id "
            f"LEFT JOIN main.event_click ec on base_event.id = ec.event_id "
            f"LEFT JOIN main.event_key_pressed ekp on base_event.id = ekp.event_id "
            f"LEFT JOIN main.event_key_release ekr on base_event.id = ekr.event_id "
            f"LEFT JOIN main.event_launch el on base_event.id = el.event_id "
            f"LEFT JOIN main.event_write ew on base_event.id = ew.event_id "
            f"WHERE base_event.macro_id = ? "
            f"ORDER BY base_event.position LIMIT {start}, {end}",
            (macro_id,), fetchall=True)