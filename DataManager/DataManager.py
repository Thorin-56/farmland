import sqlite3


class DataManager:
    def __init__(self):
        self.file = "point.db"
        self.db = sqlite3.connect(self.file, check_same_thread=False)
        self.db.execute("PRAGMA foreign_keys = ON")

        self.__initFile__()

    def __execute__(self, query, params=(), fetchall=False, fetchone=False) -> tuple[int, list | None]:
        assert not (fetchall and fetchone)
        if params is None:
            params = []
        elif isinstance(params, tuple):
            params = list(params)
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
        self.__execute__("""create table IF NOT EXISTS positions
                            (
                                id                integer not null
                                    constraint Positions_pk
                                        primary key autoincrement
                                    constraint Positions_pk_2
                                        unique,
                                base              TEXT    not null,
                                windows_name      TEXT,
                                x_pourcent_width  INTEGER not null,
                                x_pourcent_height INTEGER not null,
                                x_value           INTEGER not null,
                                y_pourcent_width  INTEGER not null,
                                y_pourcent_height INTEGER not null,
                                y_value           INTEGER not null
                            );""")

    def addMacro(self, name, categorie) -> tuple[int]:
        return self.__execute__("INSERT INTO macros (name, categorie) VALUES (?, ?)", (name, categorie))

    def addEvent(self, e_type, time, data, macro_id, position) -> tuple[int]:
        return self.__execute__("INSERT INTO events (type, time, macro_id, data, position) VALUES (?, ?, ?, ?, ?)", (e_type, time, macro_id, data, position*1000))

    def addPosition(self, base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, event_id) -> tuple[int]:
        return self.__execute__("INSERT INTO positions (base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, event_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (base, windows_name,
             x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, event_id))

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
        return self.__execute__(f"UPDATE events SET {", ".join([f"{key} = {f"\"{value}\"" if key == "data" else value}" for key, value in data.items()])} WHERE id = ?", (event_id, ))

    def updateCategories(self, categorie_id, data: dict) -> tuple[int, list]:
        return self.__execute__(f"UPDATE categories SET {", ".join([f"{key} = {value}" for key, value in data.items()])} WHERE id = ?", (categorie_id, ))

    def insertEvent(self, _id, e_type, time, data, macro_id):
        if _id is not None:
            pos_1 = self.__execute__("SELECT position FROM events WHERE id = ?", (_id, ), fetchone=True)[1][0][0]
        else:
            pos_1 = 1
        pos_2 = self.__execute__("SELECT position FROM events WHERE position > ? AND macro_id = ?", (pos_1, macro_id), fetchone=True)[1]
        if pos_2:
            pos_2 = pos_2[0][0]
        else:
            pos_2 = pos_1 + 2000
        if pos_2:
            position = pos_1 + ((pos_2 - pos_1) // 2)
        else:
            position = pos_1 + 1000
        return self.__execute__("INSERT INTO events (type, time, macro_id, data, position) VALUES (?, ?, ?, ?, ?)", (e_type, time, macro_id, data, position))

    def getMacro(self, _id):
        return self.__execute__("SELECT * FROM macros WHERE id = ?", (_id, ), fetchone=True)