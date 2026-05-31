import sqlite3

from Types.Listerners.Pos import Pos

class DataManager:
    def __init__(self):
        self.file = "point.db"
        self.db = sqlite3.connect(self.file)
        self.db.row_factory = sqlite3.Row
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
            return resut.lastrowid, resut.fetchone()
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
        self.__execute__("""create table IF NOT EXISTS base_event
                            (
                                id       integer not null
                                    constraint base_event_pk_2
                                        primary key autoincrement,
                                type     TEXT    not null,
                                time     integer not null,
                                macro_id integer not null
                                    constraint base_event_macros_id_fk
                                        references macros
                                        on delete restrict,
                                position integer not null
                            );
                         """)
        self.__execute__("""create table IF NOT EXISTS event_click
                            (
                                event_id integer not null
                                    constraint event_click_pk
                                        primary key
                                    constraint event_click_base_event_id_fk
                                        references base_event
                                        on delete cascade,
                                button   TEXT default 'left',
                                position integer not null
                                    constraint event_click_positions_id_fk
                                        references positions
                                        on delete cascade
                            );
                         """)
        self.__execute__("""create table IF NOT EXISTS event_key_pressed
                            (
                                event_id integer not null
                                    constraint event_key_pressed_pk
                                        primary key
                                    constraint event_key_pressed_base_event_id_fk
                                        references base_event
                                        on delete cascade,
                                key      TEXT    not null
                            );

                         """)
        self.__execute__("""create table IF NOT EXISTS event_key_release
                            (
                                event_id integer
                                    constraint event_key_release_pk
                                        primary key
                                    constraint event_key_release_base_event_id_fk
                                        references base_event
                                        on delete cascade,
                                key      text
                            );""")
        self.__execute__("""create table IF NOT EXISTS event_launch
                            (
                                event_id integer not null
                                    constraint event_launch_pk
                                        primary key
                                    constraint event_launch_base_event_id_fk
                                        references base_event
                                        on delete cascade,
                                macro    integer not null
                            );
                         """)
        self.__execute__("""create table IF NOT EXISTS event_move
                            (
                                event_id             integer           not null
                                    constraint event_move_base_event_id_fk
                                        references base_event
                                        on delete cascade,
                                position_source      integer           not null
                                    constraint event_move_positions_id_fk
                                        references positions
                                        on delete cascade,
                                position_destination integer           not null
                                    constraint event_move_positions_id_fk_2
                                        references positions
                                        on delete cascade,
                                duration             integer default 0 not null
                            );""")
        self.__execute__("""create table IF NOT EXISTS event_write
                            (
                                event_id integer not null
                                    constraint event_write_pk
                                        primary key
                                    constraint event_write_base_event_id_fk
                                        references base_event
                                        on delete cascade,
                                text     TEXT    not null
                            );
                         """)
        self.__execute__("""create table IF NOT EXISTS positions_new
                            (
                                id                INTEGER       not null
                                    constraint positions_new_pk
                                        primary key autoincrement,
                                base              TEXT,
                                windows_name      TEXT,
                                x_pourcent_width  INT default 0 not null,
                                x_pourcent_height INT default 0 not null,
                                x_value           INT default 0 not null,
                                y_pourcent_width  INT default 0 not null,
                                y_pourcent_height INT default 0 not null,
                                y_value           INT default 0 not null,
                                margin_left       INT default 0 not null,
                                margin_right      INT default 0 not null,
                                margin_top        INT default 0 not null,
                                margin_bottom     INT default 0 not null
                            );""")

    def addMacro(self, name, categorie) -> tuple[int]:
        return self.__execute__("INSERT INTO macros (name, categorie) VALUES (?, ?)", (name, categorie))

    def addEvent(self, e_type, time, macro_id, position) -> tuple[int]:
        return self.__execute__(f"INSERT INTO base_event (type, time, macro_id, position) VALUES (?, ?, ?, ?)",
                                (e_type, time, macro_id, position))

    def addEventClick(self, time, macro_id, button, position: Pos, order):
        base_event_id = self.addEvent("click", time, macro_id, order)[0]
        position_id = self.addPosition(position.base, position.windows_name, position.x_pourcent_width,
                                       position.x_pourcent_height, position.x_value,
                                       position.y_pourcent_width, position.y_pourcent_height, position.y_value,
                                       *position.margins)[0]
        return self.__execute__(f"INSERT INTO event_click (event_id, button, position) VALUES (?, ?, ?)",
                                (base_event_id, button, position_id))

    def addEventKeyPressed(self, time, macro_id, key, order):
        base_event_id = self.addEvent("key", time, macro_id, order)[0]
        return self.__execute__(f"INSERT INTO event_key_pressed (event_id, key) VALUES (?, ?)",
                                (base_event_id, key))

    def addEventKeyRelease(self, time, macro_id, key, order):
        base_event_id = self.addEvent("key release", time, macro_id, order)[0]
        return self.__execute__(f"INSERT INTO event_key_release (event_id, key) VALUES (?, ?)",
                                (base_event_id, key))

    def addEventWrite(self, time, macro_id, text, order):
        base_event_id = self.addEvent("write", time, macro_id, order)[0]
        return self.__execute__(f"INSERT INTO event_write (event_id, text) VALUES (?, ?)",
                                (base_event_id, text))

    def addEventLaunch(self, time, macro_id, macro, order):
        base_event_id = self.addEvent("launch", time, macro_id, order)[0]
        return self.__execute__(f"INSERT INTO event_launch (event_id, macro) VALUES (?, ?)",
                                (base_event_id, macro))

    def addEventMove(self, time, macro_id, position_source: Pos, position_destination: Pos, duration, order):
        base_event_id = self.addEvent("launch", time, macro_id, order)[0]
        position_source_id = self.addPosition(position_source.base, position_source.windows_name, position_source.x_pourcent_width,
                                       position_source.x_pourcent_height, position_source.x_value,
                                       position_source.y_pourcent_width, position_source.y_pourcent_height, position_source.y_value,
                                       *position_source.margins)[0]
        position_destination_id = self.addPosition(position_destination.base, position_destination.windows_name, position_destination.x_pourcent_width,
                                       position_destination.x_pourcent_height, position_destination.x_value,
                                       position_destination.y_pourcent_width, position_destination.y_pourcent_height, position_destination.y_value,
                                       *position_destination.margins)[0]
        return self.__execute__(f"INSERT INTO event_move (event_id, position_source, position_destination, duration) VALUES (?, ?, ?, ?)",
                                (base_event_id, position_source_id, position_destination_id, duration))

    def addPosition(self, base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width,
                    y_pourcent_height, y_value, margin_left, margin_right, margin_top, margin_bottom) -> tuple[int]:
        return self.__execute__(
            "INSERT INTO positions_new (base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, margin_left, margin_right, margin_top, margin_bottom) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height,
             y_value, margin_left, margin_right, margin_top, margin_bottom))

    def addCategorie(self, name) -> tuple[int]:
        return self.__execute__("INSERT INTO categories (name) VALUES (?)", (name,))

    def getMacroOfCategorie(self, categorie) -> tuple[int, list]:
        return self.__execute__("SELECT * FROM macros JOIN categories ON categorie=categories.id WHERE categorie = ?",
                                (categorie,), fetchall=True)

    def getEventOfMacro(self, macro_id, start=0, end=-1) -> tuple[int, list]:
        return self.__execute__(
            f"SELECT base_event.id, type, time, base_event.position as _order, "
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

    def getPosition(self, position_id):
        return self.__execute__(f"SELECT * FROM positions_new WHERE id = ?", (position_id, ), fetchone=True)

    def getCategories(self) -> tuple[int, list]:
        return self.__execute__("SELECT * FROM categories", fetchall=True)

    def getInfoOfMacro(self, macro_id) -> tuple[int, list]:
        return self.__execute__(
            "SELECT macros.*, categories.* FROM macros JOIN categories ON categorie=categories.id WHERE macros.id = ?",
            (macro_id,), fetchone=True)

    def deleteMacro(self, macro_id) -> tuple[int]:
        return self.__execute__("DELETE FROM macros WHERE id = ?", (macro_id,))

    def deleteEvent(self, event_id) -> tuple[int]:
        self.__execute__("DELETE FROM events WHERE id = ?", (event_id,))

    def deleteCategories(self, categorie_id) -> tuple[int, list]:
        return self.__execute__("DELETE FROM categories WHERE id = ?", (categorie_id,))

    def updateMacro(self, macro_id, data: dict) -> tuple[int]:
        return self.__execute__(
            f"UPDATE macros SET {", ".join([f"{key} = {value}" for key, value in data.items()])} WHERE id = ?",
            (macro_id,))

    def updateEvent(self, event_id, data: dict) -> tuple[int]:
        names = data.keys()
        values = data.values()
        return self.__execute__(
            f"UPDATE events SET {", ".join([f"{key} = ?" for key in names])} WHERE id = ?",
            (*values, event_id,))

    def updatePosition(self, event_id, data: dict) -> tuple[int]:
        names = data.keys()
        values = data.values()
        return self.__execute__(
            f"UPDATE positions SET {", ".join([f"{key} = ?" for key in names])} WHERE event_id = ?",
            (*values, event_id,))

    def updateCategories(self, categorie_id, data: dict) -> tuple[int, list]:
        return self.__execute__(
            f"UPDATE categories SET {", ".join([f"{key} = {value}" for key, value in data.items()])} WHERE id = ?",
            (categorie_id,))

    def insertEvent(self, _id, e_type, time, data, macro_id):
        if _id is not None:
            pos_1 = self.__execute__("SELECT position FROM events WHERE id = ?", (_id,), fetchone=True)[1][0][0]
        else:
            pos_1 = 1
        pos_2 = self.__execute__("SELECT position FROM events WHERE position > ? AND macro_id = ?", (pos_1, macro_id),
                                 fetchone=True)[1]
        if pos_2:
            pos_2 = pos_2[0][0]
        else:
            pos_2 = pos_1 + 2000
        if pos_2:
            position = pos_1 + ((pos_2 - pos_1) // 2)
        else:
            position = pos_1 + 1000
        return self.__execute__("INSERT INTO events (type, time, macro_id, data, position) VALUES (?, ?, ?, ?, ?)",
                                (e_type, time, macro_id, data, position))

    def getMacro(self, _id):
        return self.__execute__("SELECT * FROM macros WHERE id = ?", (_id,), fetchone=True)
