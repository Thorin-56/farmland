import asyncio
import copy

import pynput.keyboard
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from Listerners.Event import Event, EventKey, EventClick, EventKeyRelease, EventLaunch
from GuiObjects.QObjects import QScroll, QBindKeyButton
from pynput.keyboard import KeyCode, Key
import qasync

from Listerners.Listener import Listener

TABLE = {
    "key": lambda x, y: f"({x}, {x}, {y})",
    "key release": lambda x, y: f"({x}, {y}, {x})",
    "click": lambda x, y: f"({y}, {x}, {x})",
    "launch": lambda x, y: f"({y}, {x}, {y})",
    "edit": lambda x, y: f"({y}, {y}, {y})",
}

class QEvent(QWidget):

    key_selecteur: QPushButton
    save_btn: QPushButton
    def __init__(self, event: Event):
        super().__init__()

        self.event_original = event
        self.event_value = event
        self.setFixedHeight(30)

        self.save_callbakc = lambda: None

        self.hbox = QHBoxLayout()
        self.hbox.setContentsMargins(0, 0, 0, 0)

        self.main_frame = QFrame(self)
        self.frame_btn = QFrame(self)

        self.main_frame.setStyleSheet(f"background: rgb{TABLE[event.type](20, 200)}; border-radius: 5px ")


        self.frame_btn.setStyleSheet("QFrame { background: rgb(50, 50, 50); border-radius: 5px }")

        self.label_event = QLabel(event.__str__(), self.main_frame)
        self.label_event.setGeometry(5, 0, 250, 30)

        self.config_area = QScroll(self.main_frame)
        self.config_area.setGeometry(5, 35, 250, 250)
        self.config_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.config_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.config_area.vbox.setContentsMargins(0, 0, 0, 0)

        self.edit_btn = QPushButton("📝", self.frame_btn)
        self.edit_btn.setGeometry(0, 0, 30, 30)

        self.delete_btn = QPushButton("🗑️", self.frame_btn)
        self.delete_btn.setGeometry(30, 0, 30, 30)

        self.add_btn = QPushButton("➕", self.frame_btn)
        self.add_btn.setGeometry(60, 0, 30, 30)

        self.setLayout(self.hbox)
        self.hbox.addWidget(self.main_frame, 3)
        self.hbox.addWidget(self.frame_btn, 1)

    def setEditCallback(self, func):
        self.edit_btn.clicked.connect(func)

    def setDeleteCallback(self, func):
        self.delete_btn.clicked.connect(func)

    def setAddCallback(self, func):
        self.add_btn.clicked.connect(func)

    def setSaveCallback(self, func):
        self.save_callbakc = func

    def setEditMode(self):
        self.event_value = copy.deepcopy(self.event_original)
        self.setFixedHeight(250)

        frame_time = QFrame()
        frame_time.setFixedHeight(30)
        frame_time.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px ")

        label_time = QLabel("Temps:", frame_time)
        time = QDoubleSpinBox(frame_time)
        time.setRange(0, 9999)
        time.setSingleStep(0.01)
        time.setValue(self.event_value.time)
        time.valueChanged.connect(lambda x: self.event_value.__setattr__("time", round(x, 2)))

        label_time.setGeometry(5, 0, 50, 30)
        time.setGeometry(55, 0, 90, 30)
        self.config_area.add(frame_time, "time")

        if self.event_value.type == "click":
            assert isinstance(self.event_value, EventClick)
            frame_pos = QFrame()
            frame_pos.setFixedHeight(30)
            frame_pos.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px ")

            label_frame_pos = QLabel("Pos x, y:", frame_pos)
            pos_x = QSpinBox(frame_pos)
            pos_x.setRange(-9999, 9999)
            pos_x.setValue(self.event_value.pos[0])

            pos_y = QSpinBox(frame_pos)
            pos_y.setRange(-9999, 9999)
            pos_y.setValue(self.event_value.pos[1])

            label_frame_pos.setGeometry(5, 0, 50, 30)
            pos_x.setGeometry(55, 0, 90, 30)
            pos_y.setGeometry(150, 0, 90, 30)
            self.config_area.add(frame_pos, "pos")

            frame_btn = QFrame()
            frame_btn.setFixedHeight(30)
            frame_btn.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px")

            label_frame_btn = QLabel("Button:", frame_btn)
            btn_combo = QComboBox(frame_btn)
            btn_combo.addItems(("left", "right", "middle"))

            label_frame_btn.setGeometry(5, 0, 50, 30)
            btn_combo.setGeometry(55, 0, 150, 30)
            self.config_area.add(frame_btn, "btn")

        if self.event_value.type == "key" or self.event_value.type == "key release":
            assert isinstance(self.event_value, EventKey | EventKeyRelease)
            frame_key = QFrame()
            frame_key.setFixedHeight(30)
            frame_key.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px ")

            label_frame_key = QLabel("Touche:", frame_key)
            self.key_selecteur = QPushButton(self.event_value.key.__str__(), frame_key)
            self.key_selecteur.setStyleSheet(f"""
                QPushButton{{ background: rgb{TABLE[self.event_value.type](0, 170)}; border-radius: 5px }} 
                QPushButton:hover{{ background: rgb{TABLE[self.event_value.type](0, 100)}; }}
            """)
            self.key_selecteur.clicked.connect(self.setKey)

            label_frame_key.setGeometry(5, 0, 50, 30)
            self.key_selecteur.setGeometry(55, 5, 90, 20)
            self.config_area.add(frame_key, "key")

        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedHeight(30)
        self.save_btn.clicked.connect(self.save_callbakc)
        self.save_btn.setStyleSheet(f"""
                        QPushButton{{ background: rgb{TABLE[self.event_value.type](0, 170)}; border-radius: 5px }} 
                        QPushButton:hover{{ background: rgb{TABLE[self.event_value.type](0, 100)}; }}
                    """)

        self.config_area.add(self.save_btn, "save")

    @qasync.asyncSlot()
    async def setKey(self):
        self.key_selecteur.setText("...")
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.setKey2)

    def setKey2(self):
        def getKey(key: Key | KeyCode | None):
            assert isinstance(self.event_value, EventKey | EventKeyRelease)
            self.key_selecteur.setText(key.__str__())
            self.event_value.key = key
            ls.stop()
        ls = pynput.keyboard.Listener(on_press=getKey)
        ls.start()
        ls.join()


class QNowEvent(QFrame):

    def __init__(self):
        super().__init__()
        self.setFixedHeight(250)

        self.setStyleSheet(f"background: rgb{TABLE["edit"](0, 150)}; border-radius: 5px")

        self.event = EventLaunch("", "", 0.0)

        self.vbox = QVBoxLayout()
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.frame_type = QFrame()
        self.frame_type.setFixedHeight(30)
        self.frame_type.setStyleSheet(f"background: rgb{TABLE["edit"](0, 125)}; border-radius: 5px")

        self.label_type = QLabel("Type: ", self.frame_type)
        self.label_type.setGeometry(5, 0, 100, 30)

        self.combo_type = QComboBox(self.frame_type)
        self.combo_type.addItems(("click", "key", "key release", "launch"))
        self.combo_type.setGeometry(110, 0, 100, 30)
        self.combo_type.currentTextChanged.connect(self.typeChange)

        self.arg_vbox = QScroll()
        self.arg_vbox.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.arg_vbox.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        frame_categ: QFrame
        label_categ: QLabel

        self.vbox.addWidget(self.frame_type)
        self.vbox.addWidget(self.arg_vbox)

        self.setLayout(self.vbox)

    def setType(self, _type):
        self.arg_vbox.clear()
        match _type:
            case "launch":
                self.frame_categ = QFrame()
                self.frame_categ.setFixedHeight(30)
                self.frame_categ.setStyleSheet(f"background: rgb{TABLE["edit"](0, 125)}; border-radius: 5px")

                self.label_categ = QLabel("Categ: ", self.frame_categ)
                self.label_categ.setGeometry(5, 0, 100, 30)

                self.edit_categ = QLineEdit(self.frame_categ)
                self.edit_categ.setStyleSheet(f"background: rgb{TABLE["edit"](0, 100)}; border-radius: 5px")
                self.edit_categ.setGeometry(110, 5, 100, 20)

                self.frame_name = QFrame()
                self.frame_name.setFixedHeight(30)
                self.frame_name.setStyleSheet(f"background: rgb{TABLE["edit"](0, 125)}; border-radius: 5px")

                self.label_name = QLabel("Nom: ", self.frame_name)
                self.label_name.setGeometry(5, 0, 100, 30)

                self.edit_name = QLineEdit(self.frame_name)
                self.edit_name.setStyleSheet(f"background: rgb{TABLE["edit"](0, 100)}; border-radius: 5px")
                self.edit_name.setGeometry(110, 5, 100, 20)

                self.arg_vbox.add(self.frame_categ, "categ")
                self.arg_vbox.add(self.frame_name, "name")
            case "key" | "key release":
                self.frame_key = QFrame()
                self.frame_key.setFixedHeight(30)
                self.frame_key.setStyleSheet(f"background: rgb{TABLE["edit"](0, 125)}; border-radius: 5px")

                self.label_key = QLabel("Key: ", self.frame_key)
                self.label_key.setGeometry(5, 0, 100, 30)

                self.ls_key = False
                self.edit_key = QBindKeyButton(self.frame_key)
                self.edit_key.setStyleSheet(f"background: rgb{TABLE["edit"](0, 100)}; border-radius: 5px")
                self.edit_key.setGeometry(110, 5, 100, 20)

                self.arg_vbox.add(self.frame_key, "key")


    def typeChange(self, index):
        self.setType(index)

