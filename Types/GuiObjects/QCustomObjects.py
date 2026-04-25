import asyncio
import copy

import pynput.keyboard
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from Types.Listerners.Event import Event, EventKey, EventClick, EventKeyRelease, EventLaunch
from Types.GuiObjects.QObjects import QScroll, QBindKeyButton, QBindMouseButton
from pynput.keyboard import KeyCode, Key
import qasync

from VARS import database_manager

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
        self.label_event.setGeometry(5, 0, 300, 30)

        self.config_area = QScroll(self.main_frame)
        self.config_area.setGeometry(5, 35, 300, 250)
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

        self.destroyed.connect(lambda: self.preDestroy())

    def preDestroy(self):
        if isinstance(self.event_value, EventClick):
            self.event_value.pos.stopUpdateMarges()
            self.event_value.pos.stopUpdatePoint()
            self.event_value.pos.remove_preview()

    @staticmethod
    def updateValue(func):
        def wrapper(self: QEvent, *args, **kwargs):
            result =  func(self, *args, **kwargs)
            self.save_btn.setDisabled(self.event_value.jsonify() == self.event_original.jsonify())
            return result
        return wrapper

    def setEditCallback(self, func):
        self.edit_btn.clicked.connect(func)

    def setDeleteCallback(self, func):
        self.delete_btn.clicked.connect(func)

    def setAddCallback(self, func):
        self.add_btn.clicked.connect(func)

    def setSaveCallback(self, func):
        self.save_callbakc = func

    def removeEditMode(self):
        self.setFixedHeight(30)
        self.config_area.clear()
        if self.event_value.type == "click":
            assert isinstance(self.event_value, EventClick)
            self.event_value.pos.stopUpdatePoint()
            self.event_value.pos.stopUpdateMarges()
            self.event_value.pos.remove_preview()

    def setEditMode(self):
        self.event_value = copy.deepcopy(self.event_original)
        self.setFixedHeight(300)

        frame_time = QFrame()
        frame_time.setFixedHeight(30)
        frame_time.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px ")

        label_time = QLabel("Temps:", frame_time)
        time = QDoubleSpinBox(frame_time)
        time.setRange(0, 9999)
        time.setSingleStep(0.01)
        time.setValue(self.event_value.time)
        time.valueChanged.connect(self.setTime)

        label_time.setGeometry(5, 0, 50, 30)
        time.setGeometry(55, 0, 90, 30)
        self.config_area.add(frame_time, "time")

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedHeight(30)
        self.reset_btn.clicked.connect(self.reset_value)
        self.reset_btn.setStyleSheet(f"""
                                QPushButton{{ background: rgb{TABLE[self.event_value.type](0, 170)}; border-radius: 5px }} 
                                QPushButton:hover{{ background: rgb{TABLE[self.event_value.type](0, 100)}; }}
                            """)

        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedHeight(30)
        self.save_btn.clicked.connect(self.save_callbakc)
        self.save_btn.setDisabled(True)
        self.save_btn.setStyleSheet(f"""
                                QPushButton{{ background: rgb{TABLE[self.event_value.type](0, 170)}; border-radius: 5px }} 
                                QPushButton:hover{{ background: rgb{TABLE[self.event_value.type](0, 100)}; }}
                            """)

        if self.event_value.type == "click":
            assert isinstance(self.event_value, EventClick)
            frame_pos_margins = QFrame()
            frame_pos_margins.setFixedHeight(30)
            frame_pos_margins.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px ")

            label_frame_pos_margins = QLabel("Margins:", frame_pos_margins)
            # Position X Start
            pos_margins_x_start = QSpinBox(frame_pos_margins)
            pos_margins_x_start.setRange(0, 1000)
            pos_margins_x_start.setValue(self.event_value.pos.margins[0])
            pos_margins_x_start.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            # Position X End
            pos_margins_x_end = QSpinBox(frame_pos_margins)
            pos_margins_x_end.setRange(0, 1000)
            pos_margins_x_end.setValue(self.event_value.pos.margins[1])
            pos_margins_x_end.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            # Position Y Start
            pos_margins_y_start = QSpinBox(frame_pos_margins)
            pos_margins_y_start.setRange(0, 1000)
            pos_margins_y_start.setValue(self.event_value.pos.margins[2])
            pos_margins_y_start.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            # Position Y End
            pos_margins_y_end = QSpinBox(frame_pos_margins)
            pos_margins_y_end.setRange(0, 1000)
            pos_margins_y_end.setValue(self.event_value.pos.margins[3])
            pos_margins_y_end.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            view_margin = QCheckBox("Voir les marges", frame_pos_margins)

            pos_margins_x_start.valueChanged.connect(lambda value: self.setMargins(0, value))
            pos_margins_x_end.valueChanged.connect(lambda value: self.setMargins(1, value))
            pos_margins_y_start.valueChanged.connect(lambda value: self.setMargins(2, value))
            pos_margins_y_end.valueChanged.connect(lambda value: self.setMargins(3, value))
            view_margin.stateChanged.connect(self.setViewMargin)

            label_frame_pos_margins.setGeometry(5, 0, 30, 30)
            pos_margins_x_start.setGeometry(40, 0, 30, 30)
            pos_margins_x_end.setGeometry(75, 0, 30, 30)
            pos_margins_y_start.setGeometry(110, 0, 30, 30)
            pos_margins_y_end.setGeometry(145, 0, 30, 30)
            view_margin.setGeometry(180, 0, 100, 30)

            self.config_area.add(frame_pos_margins, "margins")

            frame_pos_x = QFrame()
            frame_pos_x.setFixedHeight(30)
            frame_pos_x.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px ")

            label_frame_pos_x = QLabel("Pos X:", frame_pos_x)
            # Position X Pourcent Width
            pos_x_pw = QDoubleSpinBox(frame_pos_x)
            pos_x_pw.setRange(-100, 100)
            pos_x_pw.setSingleStep(0.01)
            pos_x_pw.setValue(self.event_value.pos.x_pourcent_width)
            pos_x_pw.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            # Position X Pourcent Height
            pos_x_ph = QDoubleSpinBox(frame_pos_x)
            pos_x_ph.setRange(-100, 100)
            pos_x_ph.setSingleStep(0.01)
            pos_x_ph.setValue(self.event_value.pos.x_pourcent_height)
            pos_x_ph.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            # Position X Value
            pos_x = QSpinBox(frame_pos_x)
            pos_x.setRange(-9999, 9999)
            pos_x.setValue(self.event_value.pos.x_value)
            pos_x.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            frame_pos_y = QFrame()
            frame_pos_y.setFixedHeight(30)
            frame_pos_y.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px ")

            label_frame_pos_y = QLabel("Pos Y:", frame_pos_y)
            # Position Y Pourcent Width
            pos_y_pw = QDoubleSpinBox(frame_pos_y)
            pos_y_pw.setRange(-100, 100)
            pos_y_pw.setSingleStep(0.01)
            pos_y_pw.setValue(self.event_value.pos.y_pourcent_width)
            pos_y_pw.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            # Position Y Pourcent Height
            pos_y_ph = QDoubleSpinBox(frame_pos_y)
            pos_y_ph.setRange(-100, 100)
            pos_y_ph.setValue(self.event_value.pos.y_pourcent_height)
            pos_y_ph.setSingleStep(0.01)
            pos_y_ph.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            # Position Y Value
            pos_y = QSpinBox(frame_pos_y)
            pos_y.setRange(-9999, 9999)
            pos_y.setValue(self.event_value.pos.y_value)
            pos_y.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            label_frame_pos_x.setGeometry(5, 0, 30, 30)
            pos_x_ph.setGeometry(55, 0, 50, 30)
            pos_x_pw.setGeometry(110, 0, 50, 30)
            pos_x.setGeometry(165, 0, 50, 30)

            label_frame_pos_y.setGeometry(5, 0, 50, 30)
            pos_y_ph.setGeometry(55, 0, 50, 30)
            pos_y_pw.setGeometry(110, 0, 50, 30)
            pos_y.setGeometry(165, 0, 50, 30)

            if self.event_value.pos.windows_name is None:
                pos_x_pw.setDisabled(True)
                pos_y_pw.setDisabled(True)
                pos_x_ph.setDisabled(True)
                pos_y_ph.setDisabled(True)

            pos_x.valueChanged.connect(self.setPositionX)
            pos_y.valueChanged.connect(self.setPositionY)
            pos_x_pw.valueChanged.connect(self.setPosXpw)
            pos_y_pw.valueChanged.connect(self.setPosYpw)
            pos_x_ph.valueChanged.connect(self.setPosXph)
            pos_y_ph.valueChanged.connect(self.setPosYph)
            self.config_area.add(frame_pos_x, "pos x")
            self.config_area.add(frame_pos_y, "pos y")

            frame_btn = QFrame()
            frame_btn.setFixedHeight(30)
            frame_btn.setStyleSheet(f"background: rgb{TABLE[self.event_value.type](0, 150)}; border-radius: 5px")

            label_frame_btn = QLabel("Button:", frame_btn)
            btn_combo = QComboBox(frame_btn)
            btn_combo.addItems(("left", "right", "middle"))

            label_frame_btn.setGeometry(5, 0, 50, 30)
            btn_combo.setGeometry(55, 0, 150, 30)
            btn_combo.currentTextChanged.connect(self.setBtn)
            btn_combo.setCurrentText(self.event_value.btn)
            self.config_area.add(frame_btn, "btn")

            self.event_value.pos.startUpdatePoint()

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

        self.config_area.add(self.reset_btn, "reset")
        self.config_area.add(self.save_btn, "save")

    @updateValue
    def reset_value(self):
        self.config_area.clear()
        self.setEditMode()
        if self.event_value.type == "click":
            assert isinstance(self.event_value, EventClick)

    @qasync.asyncSlot()
    async def setKey(self):
        self.key_selecteur.setText("...")
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.setKey2)

    @updateValue
    def setMargins(self, index, value):
        assert isinstance(self.event_value, EventClick)
        self.event_value.pos.margins[index] = value

    def setViewMargin(self, value):
        assert isinstance(self.event_value, EventClick)
        print(value)
        if value:
            self.event_value.pos.startUpdateMarges()
        else:
            self.event_value.pos.stopUpdateMarges()


    @updateValue
    def setPositionX(self, value):
        assert isinstance(self.event_value, EventClick)
        self.event_value.pos.x_value = value

    @updateValue
    def setPositionY(self, value):
        assert isinstance(self.event_value, EventClick)
        self.event_value.pos.y_value = value

    @updateValue
    def setPosXpw(self, value):
        assert isinstance(self.event_value, EventClick)
        self.event_value.pos.x_pourcent_width = round(value, 2)

    @updateValue
    def setPosYpw(self, value):
        assert isinstance(self.event_value, EventClick)
        self.event_value.pos.y_pourcent_width = round(value, 2)

    @updateValue
    def setPosXph(self, value):
        assert isinstance(self.event_value, EventClick)
        self.event_value.pos.x_pourcent_height = round(value, 2)

    @updateValue
    def setPosYph(self, value):
        assert isinstance(self.event_value, EventClick)
        self.event_value.pos.y_pourcent_height = round(value, 2)

    @updateValue
    def setBtn(self, value):
        assert isinstance(self.event_value, EventClick)
        self.event_value.btn = value

    @updateValue
    def setTime(self, value):
        self.event_value.time = round(value, 2)

    @updateValue
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
    save_btn: QPushButton
    def __init__(self):
        super().__init__()
        self.setFixedHeight(275)

        self.setStyleSheet(f"background: rgb{TABLE["edit"](0, 150)}; border-radius: 5px")

        self.current_event = EventLaunch("", "", 0.0)

        self.save_callback = None
        self.cancel_callback = None

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

        self.setType("click")

    @staticmethod
    def updateValue(func):
        def wrapper(self: QNowEvent, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.save_btn.setDisabled(not self.current_event.isValable())
            return result
        return wrapper

    def setType(self, _type):
        self.arg_vbox.clear()
        self.setStyleSheet(f"background: rgb{TABLE[_type](25, 75)}; border-radius: 5px")

        frame_time = QFrame()
        frame_time.setFixedHeight(30)
        frame_time.setStyleSheet(f"background: rgb{TABLE[_type](125, 125)}; border-radius: 5px")

        label_time = QLabel("Time: ", frame_time)
        label_time.setGeometry(5, 0, 100, 30)

        edit_time = QDoubleSpinBox(frame_time)
        edit_time.setRange(0, 99999)
        edit_time.setSingleStep(0.01)
        edit_time.setStyleSheet(f"background: rgb{TABLE[_type](50, 200)}; border-radius: 5px")
        edit_time.setGeometry(110, 5, 100, 20)
        edit_time.valueChanged.connect(self.setTime)

        self.arg_vbox.add(frame_time, "time")
        match _type:
            case "launch":
                self.current_event = EventLaunch(None, 0)
                self.setTypeLaunch()
            case "key":
                self.current_event = EventKey(None, 0)
                self.setTypeKey()
            case "key release":
                self.current_event = EventKeyRelease(None, 0)
                self.setTypeKeyRelease()
            case "click":
                self.current_event = EventClick(None, [0, 0], 0)
                self.setTypeClick()

        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedHeight(30)
        self.save_btn.clicked.connect(self.save_event)
        self.save_btn.setDisabled(not self.current_event.isValable())
        self.save_btn.setStyleSheet(f" QPushButton {{background: rgb{TABLE[_type](0, 255)}; border-radius: 5px}} "
                               f" QPushButton:hover {{ background: rgb{TABLE[_type](0, 200)}; }}")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.setFixedHeight(30)
        self.cancel_btn.clicked.connect(self.cancel)
        self.cancel_btn.setStyleSheet(f" QPushButton {{background: rgb{TABLE[_type](0, 255)}; border-radius: 5px}} "
                               f" QPushButton:hover {{ background: rgb{TABLE[_type](0, 200)}; }}")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.arg_vbox.add(self.save_btn, "save")
        self.arg_vbox.add(self.cancel_btn, "cancel")

    def setSaveCallback(self, func):
        self.save_callback = func

    def save_event(self):
        if self.save_callback:
            self.save_callback(self.current_event)

    def setCancelCallback(self, func):
        self.cancel_callback = func

    def cancel(self):
        if self.cancel_callback:
            self.cancel_callback()

    def typeChange(self, index):
        self.setType(index)

    def setTypeLaunch(self):

        frame_categ = QFrame()
        frame_categ.setFixedHeight(30)
        frame_categ.setStyleSheet(f"background: rgb{TABLE["edit"](125, 125)}; border-radius: 5px")

        label_categ = QLabel("Categ: ", frame_categ)
        label_categ.setGeometry(5, 0, 100, 30)

        edit_categ = QComboBox(frame_categ)
        edit_categ.setStyleSheet(f"background: rgb{TABLE["launch"](50, 200)}; border-radius: 5px")
        edit_categ.setGeometry(110, 5, 100, 20)
        categories = database_manager.getCategories()[1]
        edit_categ.addItems([f"[{categorie[0]}] {categorie[1]}" for categorie in categories])

        frame_name = QFrame()
        frame_name.setFixedHeight(30)
        frame_name.setStyleSheet(f"background: rgb{TABLE["edit"](125, 125)}; border-radius: 5px")

        label_name = QLabel("Nom: ", frame_name)
        label_name.setGeometry(5, 0, 100, 30)

        edit_name = QComboBox(frame_name)
        edit_name.setStyleSheet(f"background: rgb{TABLE["launch"](50, 200)}; border-radius: 5px")
        edit_name.setGeometry(110, 5, 100, 20)
        edit_name.addItems([f"[{macro[0]}] {macro[1]}" for macro in database_manager.getMacroOfCategorie(categories[0][0])[1]])

        edit_categ.currentTextChanged.connect(lambda text: [edit_name.clear(), edit_name.addItems([f"[{macro[0]}] {macro[1]}" for macro in database_manager.getMacroOfCategorie(text[1:text.index(']')])[1] ])])
        edit_name.currentTextChanged.connect(lambda text: self.setMacro( int(text[1:text.index(']')]) if text else None ))

        edit_name.setCurrentIndex(-1)
        edit_name.setCurrentIndex(0)

        self.arg_vbox.add(frame_categ, "categ")
        self.arg_vbox.add(frame_name, "name")


    def setTypeKey(self):
        frame_key = QFrame()
        frame_key.setFixedHeight(30)
        frame_key.setStyleSheet(f"background: rgb{TABLE["key"](125, 125)}; border-radius: 5px")

        label_key = QLabel("Key: ", frame_key)
        label_key.setGeometry(5, 0, 100, 30)

        edit_key = QBindKeyButton(frame_key)
        edit_key.setStyleSheet(f"background: rgb{TABLE["key"](50, 200)}; border-radius: 5px")
        edit_key.setGeometry(110, 5, 100, 20)
        edit_key.changed.connect(self.setKey)

        self.arg_vbox.add(frame_key, "key")

    def setTypeKeyRelease(self):
        frame_key = QFrame()
        frame_key.setFixedHeight(30)
        frame_key.setStyleSheet(f"background: rgb{TABLE["key release"](125, 125)}; border-radius: 5px")

        label_key = QLabel("Key: ", frame_key)
        label_key.setGeometry(5, 0, 100, 30)

        edit_key = QBindKeyButton(frame_key)
        edit_key.setStyleSheet(f"background: rgb{TABLE["key release"](50, 200)}; border-radius: 5px")
        edit_key.setGeometry(110, 5, 100, 20)
        edit_key.changed.connect(self.setKey)

        self.arg_vbox.add(frame_key, "key")

    def setTypeClick(self):
        frame_click = QFrame()
        frame_click.setFixedHeight(30)
        frame_click.setStyleSheet(f"background: rgb{TABLE["click"](125, 125)}; border-radius: 5px")

        label_click = QLabel("Bouton: ", frame_click)
        label_click.setGeometry(5, 0, 100, 30)

        edit_click = QBindMouseButton(frame_click)
        edit_click.setStyleSheet(f"background: rgb{TABLE["click"](50, 200)}; border-radius: 5px")
        edit_click.setGeometry(110, 5, 100, 20)
        edit_click.changed.connect(self.setBtn)

        frame_pos_x = QFrame()
        frame_pos_x.setFixedHeight(30)
        frame_pos_x.setStyleSheet(f"background: rgb{TABLE["click"](125, 125)}; border-radius: 5px")

        label_pos_x = QLabel("Position X: ", frame_pos_x)
        label_pos_x.setGeometry(5, 0, 100, 30)

        edit_pos_x = QSpinBox(frame_pos_x)
        edit_pos_x.setRange(-9999, 9999)
        edit_pos_x.setStyleSheet(f"background: rgb{TABLE["click"](50, 200)}; border-radius: 5px")
        edit_pos_x.setGeometry(110, 5, 100, 20)
        edit_pos_x.valueChanged.connect(self.setPosX)

        frame_pos_y = QFrame()
        frame_pos_y.setFixedHeight(30)
        frame_pos_y.setStyleSheet(f"background: rgb{TABLE["click"](125, 125)}; border-radius: 5px")

        label_pos_y = QLabel("Position Y: ", frame_pos_y)
        label_pos_y.setGeometry(5, 0, 100, 30)

        edit_pos_y = QSpinBox(frame_pos_y)
        edit_pos_y.setRange(-9999, 9999)
        edit_pos_y.setStyleSheet(f"background: rgb{TABLE["click"](50, 200)}; border-radius: 5px")
        edit_pos_y.setGeometry(110, 5, 100, 20)
        edit_pos_x.valueChanged.connect(self.setPosY)

        self.arg_vbox.add(frame_click, "button")
        self.arg_vbox.add(frame_pos_x, "pos_x")
        self.arg_vbox.add(frame_pos_y, "pos_y")

    @updateValue
    def setBtn(self, value):
        assert isinstance(self.current_event, EventClick)
        self.current_event.btn = value.name

    @updateValue
    def setPosX(self, value):
        assert isinstance(self.current_event, EventClick)
        self.current_event.pos.x_value = value

    @updateValue
    def setPosY(self, value):
        assert isinstance(self.current_event, EventClick)
        self.current_event.pos.y_value = value

    @updateValue
    def setPosXpw(self, value):
        assert isinstance(self.current_event, EventClick)
        self.current_event.pos.x_pourcent_width = value

    @updateValue
    def setPosYpw(self, value):
        assert isinstance(self.current_event, EventClick)
        self.current_event.pos.y_pourcent_width = value

    @updateValue
    def setPosXph(self, value):
        assert isinstance(self.current_event, EventClick)
        self.current_event.pos.x_pourcent_height = value

    @updateValue
    def setPosYph(self, value):
        assert isinstance(self.current_event, EventClick)
        self.current_event.pos.y_pourcent_height = value

    @updateValue
    def setKey(self, value):
        assert isinstance(self.current_event, EventKey)
        self.current_event.key = value

    @updateValue
    def setTime(self, value):
        self.current_event.time = round(value, 2)

    @updateValue
    def setMacro(self, value):
        assert isinstance(self.current_event, EventLaunch)
        self.current_event.macro = value