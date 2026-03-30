import sqlite3


class DataManager:
    def __init__(self):
        self.file = "point.db"
        self.db = sqlite3.connect(self.file, check_same_thread=False)
        self.db.execute("PRAGMA foreign_keys = ON")

        self.__initFile__()

    def __execute__(self, query, params=(), fetchall=False, fetchone=False):
        assert not (fetchall and fetchone)
        resut = self.db.execute(query, params)
        self.db.commit()
        if fetchall:
            return resut.lastrowid, resut.fetchall()
        if fetchone:
            return resut.lastrowid, resut.fetchall()
        else:
            return resut.lastrowid,

    def __initFile__(self):
        self.__execute__("""create table IF NOT EXISTS categories
                            (
                                id   integer not null
                                    constraint categories_pk
                                        primary key autoincrement,
                                name TEXT    not null
                            );
                         """)
        self.__execute__("""create table IF NOT EXISTS macros
                            (
                                id        integer not null
                                    constraint macros_pk
                                        primary key autoincrement,
                                name      TEXT    not null,
                                categorie integer not null
                                    constraint macros_categories_id_fk
                                        references categories
                                        on update cascade on delete restrict
                            );
                         """)
        self.__execute__("""create table IF NOT EXISTS events
                            (
                                id       integer            not null
                                    constraint events_pk
                                        primary key autoincrement,
                                type     TEXT               not null,
                                time     FLOAT default 0    not null,
                                macro_id integer            not null
                                    references macros
                                        on update cascade on delete cascade,
                                data     TEXT  default '{}' not null,
                                position integer            not null,
                                constraint check_type
                                    check (type in ('key', 'key release', 'launch', 'sleep', 'click', 'move'))
                            );""")

    def addMacro(self, name, categorie) -> tuple[int]:
        return self.__execute__("INSERT INTO macros (name, categorie) VALUES (?, ?)", (name, categorie))

    def addEvent(self, e_type, time, data, macro_id, position) -> tuple[int]:
        return self.__execute__("INSERT INTO events (type, time, macro_id, data, position) VALUES (?, ?, ?, ?, ?)", (e_type, time, macro_id, data, position*1000))

    def addCategorie(self, name) -> tuple[int]:
        return self.__execute__("INSERT INTO categories (name) VALUES (?)", (name, ))

    def getMacroOfCategorie(self, categorie) -> tuple[int, list]:
        return self.__execute__("SELECT * FROM macros JOIN categories ON categorie=categories.id WHERE categorie = ?", (categorie, ), fetchall=True)

    def getEventOfMacro(self, macro_id) -> tuple[int, list]:
        return self.__execute__("SELECT events.id, type, time, macro_id, data FROM events JOIN macros ON macro_id=macros.id WHERE macro_id = ? ORDER BY position", (macro_id, ), fetchall=True)

    def getCategories(self) -> tuple[int, list]:
        return self.__execute__("SELECT * FROM categories", fetchall=True)

    def deleteMacro(self, macro_id) -> tuple[int]:
        return self.__execute__("DELETE FROM macros WHERE id = ?", (macro_id, ))

    def deleteEvent(self, event_id) -> tuple[int]:
        self.__execute__("DELETE FROM events WHERE id = ?", (event_id, ))

    def deleteCategories(self, categorie_id) -> tuple[int, list]:
        return self.__execute__("DELETE FROM categories WHERE id = ?", (categorie_id, ))

    def updateMacro(self, macro_id, data: dict) -> tuple[int]:
        return self.__execute__(f"UPDATE macros SET {", ".join([f"{key} = {value}" for key, value in data.items()])} WHERE id = ?", (macro_id, ))

    def updateEvent(self, event_id, data: dict) -> tuple[int]:
        print(f"UPDATE events SET {", ".join([f"{key} = {f"\"{value}\"" if key == "data" else value}" for key, value in data.items()])} WHERE id = ?")
        return self.__execute__(f"UPDATE events SET {", ".join([f"{key} = {f"\"{value}\"" if key == "data" else value}" for key, value in data.items()])} WHERE id = ?", (event_id, ))

    def updateCategories(self, categorie_id, data: dict) -> tuple[int, list]:
        return self.__execute__(f"UPDATE categories SET {", ".join([f"{key} = {value}" for key, value in data.items()])} WHERE id = ?", (categorie_id, ))
