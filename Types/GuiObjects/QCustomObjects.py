import copy
from typing import Generic, TypeVar

from PySide6.QtCore import Qt, Signal, QVariantAnimation
from PySide6.QtGui import QColor
from PySide6.QtWidgets import *

from Types.GuiObjects.QObjects import CompactSpinBox, CompactDoubleSpinBox, BindKeyButton, BindMouseButton
from Types.GuiObjects.QObjects import QScroll
from Types.Listerners.Event import Event, EventKey, EventClick, EventKeyRelease, EventLaunch, Pos
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
                save_button.setDisabled(self.original_event == self.event or not self.event.isValable())
            return result
        return wrapper

    @staticmethod
    def resetValue(func):
        def inner(self: ConfigItem, *args, **kwargs):
            self.event = copy.deepcopy(self.original_event)
            self.edit_time.setValue(self.event.time)
            return func(self, *args, **kwargs)
        return ConfigItem.updateValue(inner)

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

        # Button
        frame_button = self.addFrame("button")
        self.label_button = QLabel("Bouton: ")
        self.edit_button = BindMouseButton()
        frame_button.addWidget(self.label_button)
        frame_button.addWidget(self.edit_button)

        self.edit_button.changed.connect(self.setButton)

        # Margins
        self.addTitle("Marges", 'margins title')
        frame_margins = self.addFrame("margins")
        self.margin_left = CompactSpinBox(prefix="gauche: ", minimum=0, maximum=9999, singleStep=1)
        self.margin_right = CompactSpinBox(prefix="droite: ", minimum=0, maximum=9999, singleStep=1)
        self.margin_top = CompactSpinBox(prefix="haut: ", minimum=0, maximum=9999, singleStep=1)
        self.margin_bottom = CompactSpinBox(prefix="bas: ", minimum=0, maximum=9999, singleStep=1)
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

        # Preview
        frame_preview = self.addFrame("preview")
        self.edit_preview_pos = QCheckBox("Voir la position")
        self.edit_preview_margins = QCheckBox("Voir les marges")
        frame_preview.addWidget(self.edit_preview_pos)
        frame_preview.addWidget(self.edit_preview_margins)

        self.edit_preview_pos.clicked.connect(self.setPreviewPos)
        self.edit_preview_margins.clicked.connect(self.setPreviewMargins)

    @ConfigItem.resetValue
    def resetValues(self):
        self.edit_button.setValue(self.event.btn)

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

    def setPreviewPos(self, value):
        if value:
            self.event.pos.startUpdatePoint()
        else:
            self.event.pos.stopUpdatePoint()

    def setPreviewMargins(self, value):
        if value:
            self.event.pos.startUpdateMarges()
        else:
            self.event.pos.stopUpdateMarges()

    @ConfigItem.updateValue
    def setButton(self, value):
        self.event.btn = value

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
        self.edit_key = BindKeyButton()
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
        self.edit_key = BindKeyButton()
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
        macro = database_manager.getInfoOfMacro(self.event.macro)[1]
        if macro:
            macro = macro[0]
            categ_name = macro[4]
            macro_name = macro[1]
            self.edit_categorie.setCurrentText(f"[{macro[3]}] {categ_name}")
            self.edit_name.setCurrentText(f'[{macro[0]}] {macro_name}')
        else:
            self.edit_categorie.setCurrentIndex(0)
            self.edit_name.setCurrentIndex(0)


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
        self.event_value: Event = event
        self.setFixedHeight(30)

        self.save_callback = lambda: None

        self.hbox = QHBoxLayout()
        self.hbox.setContentsMargins(0, 0, 0, 0)

        self.main_frame = QFrame(self)
        self.anim = None
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
        try:
            if self.anim:
                self.anim.stop()
        except RuntimeError:
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

    def loadAnim(self, delay=0):
        self.anim = QVariantAnimation()
        self.anim.setStartValue(0.)
        self.anim.setEndValue(1.)
        self.anim.setDuration(self.event_value.time*1000-delay)
        self.anim.valueChanged.connect(lambda color: self.main_frame.setStyleSheet(
            f"*{{background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:{color} rgb{TABLE[self.event_value.type](200, 200)}, stop:{color + 0.01} rgb{TABLE[self.event_value.type](20, 200)}); border-radius: 5px }}"))
        # self.anim.valueChanged.connect(lambda x: print(x))
        self.anim.finished.connect(lambda: self.main_frame.setStyleSheet(f"*{{background: rgb{TABLE[self.event_value.type](20, 200)}; border-radius: 5px }}"))
        self.anim.start()

class EventClickItem(EventItem[EventClick]):
    _type = EventClick
    def __init__(self, event):
        super().__init__(event)

    def removeEditMode(self):
        super().removeEditMode()
        self.config_item.event.pos.stopUpdatePoint()
        self.config_item.event.pos.stopUpdateMarges()

    def preDestroy(self):
        super().preDestroy()
        self.config_item.event.pos.stopUpdateMarges()
        self.config_item.event.pos.stopUpdatePoint()


class QNowEvent(QFrame):
    save_btn: QPushButton
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: rgb{TABLE["edit"](0, 150)}; border-radius: 5px")

        self.current_event = EventLaunch("", 0.0)

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
        self.combo_type.currentTextChanged.connect(self.setType)

        self.arg_vbox = QScroll()
        self.arg_vbox.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.arg_vbox.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.config_item = ConfigItem(self.arg_vbox, self.current_event)

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

        match _type:
            case "launch":
                self.current_event = EventLaunch(None, 0.)
            case "key":
                self.current_event = EventKey(None, 0.)
            case "key release":
                self.current_event = EventKeyRelease(None, 0.)
            case "click":
                self.current_event = EventClick(None, Pos(), 0.)

        self.config_item = ConfigItem(self.arg_vbox, self.current_event)
        cancel_button = self.config_item.addButton("Annuler", "cancel")
        if cancel_button:
            cancel_button.clicked.connect(self.cancel)
        save_button: QPushButton | None = self.config_item.items.get("save")
        if save_button:
            save_button.clicked.connect(self.save_event)
        self.config_item.load()

        self.setFixedHeight(len(self.arg_vbox.items) * 36 + 60)

    def setSaveCallback(self, func):
        self.save_callback = func

    def save_event(self):
        if self.save_callback:
            self.save_callback(self.config_item.event)

    def setCancelCallback(self, func):
        self.cancel_callback = func

    def cancel(self):
        if self.cancel_callback:
            self.cancel_callback()
