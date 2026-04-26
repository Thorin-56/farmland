import copy
from typing import Generic, TypeVar

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *

from Types.GuiObjects.QObjects import CompactSpinBox, CompactDoubleSpinBox
from Types.GuiObjects.QObjects import QScroll, QBindKeyButton, QBindMouseButton
from Types.Listerners.Event import Event, EventKey, EventClick, EventKeyRelease, EventLaunch
from VARS import database_manager

TABLE = {
    "key": lambda x, y: f"({x}, {x}, {y})",
    "key release": lambda x, y: f"({x}, {y}, {x})",
    "click": lambda x, y: f"({y}, {x}, {x})",
    "launch": lambda x, y: f"({y}, {x}, {y})",
    "edit": lambda x, y: f"({y}, {y}, {y})",
}

T = TypeVar("T", bound=Event)


class Meta(type):
    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)  # exécute __init__ en entier
        instance._post_init()                               # puis seulement après
        return instance


class ConfigItem(Generic[T], metaclass=Meta):
    signal = Signal(object)
    _type = None
    def __new__(cls, parent: QScroll, event: T):
        if cls != ConfigItem:
            return object.__new__(cls)

        event_type = type(event)
        for sub in cls.__subclasses__():
            if sub._type == event_type:
                o = object.__new__(sub)
                return o
        return None

    def __init__(self, parent: QScroll, event: T):
        self.parent = parent
        self.items: dict[str, QWidget] = {}
        self.original_event = event
        self.event = copy.deepcopy(event)

        frame_time = self.addFrame("time")
        self.label_time = QLabel("Temps")
        self.edit_time = CompactDoubleSpinBox(suffix=" secondes", minimum=0, maximum=9999, singleStep=0.01)
        self.edit_time.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.edit_time.roundedValueChanged.connect(self.setTime)
        frame_time.addWidget(self.label_time)
        frame_time.addWidget(self.edit_time)

    def _post_init(self):
        reset_button = self.addButton("Reset", "reset")
        self.addButton("Sauvegarder", "save")
        if reset_button:
            reset_button.clicked.connect(lambda _: self.resetValues())
        self.resetValues()

    @staticmethod
    def updateValue(func):
        def wrapper(self: ConfigItem, *args, **kwargs):
            result =  func(self, *args, **kwargs)
            save_button = self.items.get("save")
            if save_button:
                save_button.setDisabled(self.original_event.jsonify() == self.event.jsonify())
            return result
        return wrapper

    @staticmethod
    def resetValue(func):
        def wrapper(self: ConfigItem, *args, **kwargs):
            self.event = copy.deepcopy(self.original_event)
            self.edit_time.setValue(self.event.time)
            result = func(self, *args, **kwargs)
            return result
        return wrapper

    def resetValues(self):
        self.edit_time.setValue(self.event.time)

    def addFrame(self, name) -> QHBoxLayout | None:
        if self.items.get(name):
            return None
        frame = QFrame()
        frame.setFixedHeight(30)
        frame.setStyleSheet(f"*{{background: rgb{TABLE[self.event.type](0, 150)}; border-radius: 5px}}"
                            f"QSpinBox, QDoubleSpinBox{{ background: rgb{TABLE[self.event.type](0, 125)}; padding: 0px; margin: 0px;}}")

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        frame.setLayout(layout)

        self.items.update({name: frame})
        return layout

    def addTitle(self, text, name) -> QLabel | None:
        if self.items.get(name):
            return None
        title = QLabel(text)
        title.setFixedHeight(30)
        title.setStyleSheet("font-size: 20px")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items.update({name: title})
        return title

    def addButton(self, text, name) -> QPushButton | None:
        if self.items.get(name):
            return None
        button = QPushButton(text)
        button.setFixedHeight(30)
        button.setStyleSheet(f"""
                                QPushButton{{ background: rgb{TABLE[self.event.type](0, 170)}; border-radius: 5px }} 
                                QPushButton:hover{{ background: rgb{TABLE[self.event.type](0, 100)}; }}
                            """)
        self.items.update({name: button})
        return button

    def load(self):
        for name, value in self.items.items():
            self.parent.add(value, name)

    @updateValue
    def setTime(self, value):
        self.event.time = value

class ConfigClickItem(ConfigItem[EventClick]):
    _type = EventClick
    def __init__(self, parent: QScroll, event: EventClick):
        super().__init__(parent, event)

        # Margins
        self.addTitle("Marges", 'margins title')
        frame_margins = self.addFrame("margins")
        self.margin_left = CompactSpinBox(prefix="gauche: ", minimum=0, maximum=9999, singleStep=1, value=self.event.pos.margins[0])
        self.margin_right = CompactSpinBox(prefix="droite: ", minimum=0, maximum=9999, singleStep=1, value=self.event.pos.margins[1])
        self.margin_top = CompactSpinBox(prefix="haut: ", minimum=0, maximum=9999, singleStep=1, value=self.event.pos.margins[2])
        self.margin_bottom = CompactSpinBox(prefix="bas: ", minimum=0, maximum=9999, singleStep=1, value=self.event.pos.margins[3])
        self.margin_left.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.margin_right.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.margin_top.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.margin_bottom.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.margin_left.valueChanged.connect(lambda value: self.setMargins(0, value))
        self.margin_right.valueChanged.connect(lambda value: self.setMargins(1, value))
        self.margin_top.valueChanged.connect(lambda value: self.setMargins(2, value))
        self.margin_bottom.valueChanged.connect(lambda value: self.setMargins(3, value))

        frame_margins.addWidget(self.margin_left)
        frame_margins.addWidget(self.margin_right)
        frame_margins.addWidget(self.margin_top)
        frame_margins.addWidget(self.margin_bottom)

        # Position
        self.addTitle("Position", "position title")
        frame_pos_x = self.addFrame("position x")
        self.label_pos_x = QLabel("X: ")
        self.edit_pos_x_width = CompactDoubleSpinBox(prefix="largeur: ", suffix="%", minimum=-100, maximum=100, singleStep=0.01)
        self.edit_pos_x_height = CompactDoubleSpinBox(prefix="hauteur: ", suffix="%", minimum=-100, maximum=100, singleStep=0.01)
        self.edit_pos_x_value = CompactSpinBox(prefix="ajout: ", suffix="px", minimum=-9999, maximum=9999, singleStep=1)
        frame_pos_y = self.addFrame("position y")
        self.label_pos_y = QLabel("Y: ")
        self.edit_pos_y_width = CompactDoubleSpinBox(prefix="largeur: ", suffix="%", minimum=-100, maximum=100, singleStep=0.01)
        self.edit_pos_y_height= CompactDoubleSpinBox(prefix="hauteur: ", suffix="%", minimum=-100, maximum=100, singleStep=0.01)
        self.edit_pos_y_value = CompactSpinBox(prefix="ajout: ", suffix="px", minimum=-9999, maximum=9999, singleStep=1)

        self.edit_pos_x_width.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.edit_pos_x_height.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.edit_pos_x_value.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.edit_pos_y_width.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.edit_pos_y_height.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.edit_pos_y_value.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.edit_pos_x_width.roundedValueChanged.connect(self.setPosXWidth)
        self.edit_pos_x_height.roundedValueChanged.connect(self.setPosXHeight)
        self.edit_pos_x_value.valueChanged.connect(self.setPosXValue)

        self.edit_pos_y_width.roundedValueChanged.connect(self.setPosYWidth)
        self.edit_pos_y_height.roundedValueChanged.connect(self.setPosYHeight)
        self.edit_pos_y_value.valueChanged.connect(self.setPosYValue)

        frame_pos_x.addWidget(self.label_pos_x)
        frame_pos_x.addWidget(self.edit_pos_x_width)
        frame_pos_x.addWidget(self.edit_pos_x_height)
        frame_pos_x.addWidget(self.edit_pos_x_value)

        frame_pos_y.addWidget(self.label_pos_y)
        frame_pos_y.addWidget(self.edit_pos_y_width)
        frame_pos_y.addWidget(self.edit_pos_y_height)
        frame_pos_y.addWidget(self.edit_pos_y_value)

    @ConfigItem.resetValue
    def resetValues(self):
        self.margin_left.setValue(self.event.pos.margins[0])
        self.margin_right.setValue(self.event.pos.margins[1])
        self.margin_top.setValue(self.event.pos.margins[2])
        self.margin_bottom.setValue(self.event.pos.margins[3])

        self.edit_pos_x_width.setValue(self.event.pos.x_pourcent_width)
        self.edit_pos_x_height.setValue(self.event.pos.x_pourcent_height)
        self.edit_pos_x_value.setValue(self.event.pos.x_value)
        self.edit_pos_y_width.setValue(self.event.pos.y_pourcent_width)
        self.edit_pos_y_height.setValue(self.event.pos.y_pourcent_height)
        self.edit_pos_y_value.setValue(self.event.pos.y_value)

    @ConfigItem.updateValue
    def setMargins(self, index, value):
        self.event.pos.margins[index] = value

    @ConfigItem.updateValue
    def setPosXWidth(self, value):
        self.event.pos.x_pourcent_width = value

    @ConfigItem.updateValue
    def setPosXHeight(self, value):
        self.event.pos.x_pourcent_height = value

    @ConfigItem.updateValue
    def setPosXValue(self, value):
        self.event.pos.x_value = value

    @ConfigItem.updateValue
    def setPosYWidth(self, value):
        self.event.pos.y_pourcent_width = value

    @ConfigItem.updateValue
    def setPosYHeight(self, value):
        self.event.pos.y_pourcent_height = value

    @ConfigItem.updateValue
    def setPosYValue(self, value):
        self.event.pos.y_value = value

class ConfigKeyItem(ConfigItem[EventKey]):
    _type = EventKey
    def __init__(self, parent: QScroll, event: EventKey):
        super().__init__(parent, event)

        frame_key = self.addFrame("key")
        self.label_key = QLabel("Touche: ")
        self.edit_key = QBindKeyButton()
        self.edit_key.changed.connect(self.setKey)
        frame_key.addWidget(self.label_key)
        frame_key.addWidget(self.edit_key)

    @ConfigItem.resetValue
    def resetValues(self):
        self.edit_key.setValue(self.event.key)

    @ConfigItem.updateValue
    def setKey(self, value):
        self.event.key = value

class ConfigKeyReleaseItem(ConfigItem[EventKeyRelease]):
    _type = EventKeyRelease
    def __init__(self, parent: QScroll, event: EventKeyRelease):
        super().__init__(parent, event)
        frame_key = self.addFrame("key")
        self.label_key = QLabel("Touche: ")
        self.edit_key = QBindKeyButton()
        self.edit_key.changed.connect(self.setKey)
        frame_key.addWidget(self.label_key)
        frame_key.addWidget(self.edit_key)

    @ConfigItem.resetValue
    def resetValues(self):
        self.edit_key.setValue(self.event.key)

    @ConfigItem.updateValue
    def setKey(self, value):
        self.event.key = value

class ConfigLaunchItem(ConfigItem[EventLaunch]):
    _type = EventLaunch
    def __init__(self, parent: QScroll, event: EventLaunch):
        super().__init__(parent, event)

        frame_categorie = self.addFrame("categorie")
        self.label_categorie = QLabel("Catégorie: ")
        self.edit_categorie = QComboBox()
        self.edit_categorie.setStyleSheet(f"background: rgb{TABLE["launch"](50, 200)}; border-radius: 5px; padding: 0 0 0 5px")
        categories = database_manager.getCategories()[1]
        self.edit_categorie.addItems([f"[{categorie[0]}] {categorie[1]}" for categorie in categories])

        frame_categorie.addWidget(self.label_categorie)
        frame_categorie.addWidget(self.edit_categorie)

        frame_name = self.addFrame("name")

        self.label_name = QLabel("Nom: ")

        self.edit_name = QComboBox()
        self.edit_name.setStyleSheet(
            f"background: rgb{TABLE["launch"](50, 200)}; border-radius: 5px; padding: 0 0 0 5px")
        self.edit_name.addItems(
            [f"[{macro[0]}] {macro[1]}" for macro in database_manager.getMacroOfCategorie(categories[0][0])[1]])

        self.edit_categorie.currentTextChanged.connect(lambda text: [self.edit_name.clear(), self.edit_name.addItems(
            [f"[{macro[0]}] {macro[1]}" for macro in
             database_manager.getMacroOfCategorie(text[1:text.index(']')])[1]])])
        self.edit_name.currentTextChanged.connect(lambda text: self.setMacro(int(text[1:text.index("]")]) if text else None))

        frame_name.addWidget(self.label_name)
        frame_name.addWidget(self.edit_name)

    @ConfigItem.resetValue
    def resetValues(self):
        macro = database_manager.getInfoOfMacro(self.event.macro)[1][0]
        categ_name = macro[4]
        macro_name = macro[1]
        self.edit_categorie.setCurrentText(f"[{macro[3]}] {categ_name}")
        self.edit_name.setCurrentText(f'[{macro[0]}] {macro_name}')

    @ConfigItem.updateValue
    def setMacro(self, value):
        self.event.macro = value


class EventItem(QWidget, Generic[T]):

    _type = None
    def __new__(cls, event: T):
        if cls != EventItem:
            return object.__new__(cls)

        event_type = type(event)
        for sub in cls.__subclasses__():
            if sub._type == event_type:
                o = QWidget.__new__(sub)
                return o
        return QWidget.__new__(cls)

    def __init__(self, event: T):
        super().__init__()
        self.event_value = event
        self.setFixedHeight(30)

        self.save_callback = lambda: None

        self.hbox = QHBoxLayout()
        self.hbox.setContentsMargins(0, 0, 0, 0)

        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet(f"*{{background: rgb{TABLE[event.type](20, 200)}; border-radius: 5px }}")

        self.frame_btn = QFrame(self)
        self.frame_btn.setMaximumWidth(90)
        self.frame_btn.setStyleSheet("QFrame { background: rgb(50, 50, 50); border-radius: 5px }")

        self.main_frame_vbox = QVBoxLayout()
        self.main_frame_vbox.setContentsMargins(5, 0, 5, 5)
        self.main_frame_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.main_frame.setLayout(self.main_frame_vbox)

        self.label_event = QLineEdit(event.__str__(), self.main_frame)
        self.label_event.setReadOnly(True)
        self.label_event.setFixedHeight(30)

        self.config_area = QScroll()
        self.config_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.config_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.config_area.vbox.setContentsMargins(0, 0, 0, 0)
        self.config_area.hide()

        self.main_frame_vbox.addWidget(self.label_event)
        self.main_frame_vbox.addWidget(self.config_area)

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

        self.config_item = ConfigItem(self.config_area, self.event_value)

    def preDestroy(self):
        pass

    def setEditCallback(self, func):
        self.edit_btn.clicked.connect(func)

    def setDeleteCallback(self, func):
        self.delete_btn.clicked.connect(func)

    def setAddCallback(self, func):
        self.add_btn.clicked.connect(func)

    def setSaveCallback(self, func):
        self.save_callback = func
        save_button: QPushButton = self.config_item.items.get("save")
        if save_button:
            save_button.clicked.connect(func)
            return T
        else:
            return None
    def removeEditMode(self):
        self.setFixedHeight(30)
        self.config_area.clear()
        self.config_area.hide()

    def setEditMode(self):
        self.config_area.show()

        self.config_item = ConfigItem(self.config_area, self.event_value)
        save_button: QPushButton = self.config_item.items.get("save")
        if save_button:
            save_button.clicked.connect(self.save_callback)
        self.config_item.load()

        self.setFixedHeight(len(self.config_area.items)*36 + 36)

class EventClickItem(EventItem[EventClick]):
    _type = EventClick
    def __init__(self, event):
        super().__init__(event)

    def removeEditMode(self):
        super().removeEditMode()
        self.event_value.pos.stopUpdatePoint()
        self.event_value.pos.stopUpdateMarges()

    def preDestroy(self):
        super().preDestroy()
        self.event_value.pos.stopUpdateMarges()
        self.event_value.pos.stopUpdatePoint()


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