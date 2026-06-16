import sqlite3
from Types.DataManager import Position, Categorie, Macro
from Types.DataManager.Events import Event, Click, KeyPressed, KeyRelease, Launch, Write, Move

class DataManager:
    def __init__(self):
        self.file = "point.db"
        self.db = sqlite3.connect(self.file)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")

        self.Click = Click(self)
        self.KeyPressed = KeyPressed(self)
        self.KeyRelease = KeyRelease(self)
        self.Launch = Launch(self)
        self.Move = Move(self)
        self.Write = Write(self)

        self.Position = Position(self)
        self.Event = Event(self)
        self.Categorie = Categorie(self)
        self.Macro = Macro(self)

        self.__initFile__()

    def __execute__(self, query: object, params: object = (), fetchall: object = False, fetchone: object = False) -> tuple[int, list | None]:
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
                                        on update cascade on delete cascade 
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
