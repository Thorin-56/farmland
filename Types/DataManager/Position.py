from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager

class DatabasePosition:
    def __init__(self, parent: DataManager):
        self.parent = parent

    def add(self, base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width,
            y_pourcent_height, y_value, margin_left, margin_right, margin_top, margin_bottom) -> tuple[int]:
        return self.parent.__execute__(
            "INSERT INTO positions (base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, margin_left, margin_right, margin_top, margin_bottom) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height,
             y_value, margin_left, margin_right, margin_top, margin_bottom))

    def update(self, _id, base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, margin_left, margin_right, margin_top, margin_bottom) -> tuple[int]:
        self.parent.__execute__(
            f"UPDATE positions SET base = ?, windows_name = ?, "
            f"x_pourcent_width = ?, x_pourcent_height = ?, x_value = ?, "
            f"y_pourcent_width = ?, y_pourcent_height = ?, y_value = ?, "
            f"margin_left = ?, margin_right = ?, margin_top = ?, margin_bottom = ? WHERE id = ?",
            (base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, margin_left, margin_right, margin_top, margin_bottom, _id))

    def getInsertPosition(self, _id, macro_id):
        if _id is not None:
            pos_1 = self.parent.__execute__("SELECT position FROM base_event WHERE id = ?", (_id,), fetchone=True)[1][0]
        else:
            pos_1 = 1
        pos_2 = self.parent.__execute__("SELECT position FROM base_event WHERE position > ? AND macro_id = ? ORDER BY position", (pos_1, macro_id),
                                 fetchone=True)[1]
        if pos_2:
            pos_2 = pos_2[0]
        else:
            pos_2 = pos_1 + 2000
        if pos_2:
            position = pos_1 + ((pos_2 - pos_1) // 2)
        else:
            position = pos_1 + 1000
        return position
    
    def get(self, _id):
        return self.parent.__execute__(f"SELECT * FROM positions WHERE id = ?", (_id, ), fetchone=True)