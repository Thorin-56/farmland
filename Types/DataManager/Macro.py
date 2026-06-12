from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Types.DataManager.DataManager import DataManager


class DatabaseMacro:
    def __init__(self, parent: DataManager):
        self.parent = parent

    def add(self, name, categorie):
        return self.parent.__execute__("INSERT INTO macros (name, categorie) VALUES (?, ?)", (name, categorie))

    def getMacroOfCategorie(self, categorie) -> tuple[int, list]:
        return self.parent.__execute__(
            "SELECT * FROM macros JOIN categories ON categorie=categories.id WHERE categorie = ?",
            (categorie,), fetchall=True)

    def getInfoOfMacro(self, macro_id) -> tuple[int, list]:
        return self.parent.__execute__(
            "SELECT macros.*, categories.* FROM macros JOIN categories ON categorie=categories.id WHERE macros.id = ?",
            (macro_id,), fetchone=True)

    def delete(self, macro_id):
        return self.parent.__execute__("DELETE FROM macros WHERE id = ?", (macro_id,))

    def update(self, macro_id, data: dict):
        return self.parent.__execute__(
            f"UPDATE macros SET {", ".join([f"{key} = {value}" for key, value in data.items()])} WHERE id = ?",
            (macro_id,))

    def get(self, _id):
        return self.parent.__execute__("SELECT * FROM macros WHERE id = ?", (_id,), fetchone=True)
