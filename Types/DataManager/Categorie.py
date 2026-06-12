from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager


class DatabaseCategorie:
    def __init__(self, parent: DataManager):
        self.parent = parent

    def add(self, name) -> tuple[int]:
        return self.parent.__execute__("INSERT INTO categories (name) VALUES (?)",     (name,))

    def getAlls(self) -> tuple[int, list]:
        return self.parent.__execute__("SELECT * FROM categories", fetchall=True)

    def delete(self, categorie_id) -> tuple[int, list]:
        return self.parent.__execute__("DELETE FROM categories WHERE id = ?", (categorie_id,))

    def update(self, categorie_id, data: dict) -> tuple[int, list]:
        return self.parent.__execute__(
            f"UPDATE categories SET {", ".join([f"{key} = {value}" for key, value in data.items()])} WHERE id = ?",
            (categorie_id,))
