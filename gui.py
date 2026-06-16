import asyncio
import datetime
import secrets

import qasync
from PySide6.QtCore import Signal, QRect
from PySide6.QtGui import QCloseEvent, Qt
from PySide6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFrame, QCheckBox, QComboBox, QHBoxLayout, \
    QVBoxLayout, QWidget

from Types.GuiObjects.QCustomObjects import EventItem, QNowEvent
from Types.GuiObjects.QObjects import QScrollCategorie, QScroll
from Types.Listerners.Event import ListEvent, Event
from Types.Listerners.Listener import Listener
from Types.Listerners.Pos import PosBase
from Types.Listerners.Simulator import Simulator
from Types.app_types import PosParams
from VARS import database_manager
from windows.list_monitors import list_monitors
from windows.list_windows import get_taskbar_apps


class MainWindows(QMainWindow):
    _anim_signal = Signal(object)
    _launch_anim_signal = Signal(object, object)
    _event_scroll_area_isload = Signal(object)
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoFarm")

        # Config
        self.pos_params = PosParams(False, PosBase.SCREEN, base_name=None, margins=(0, 0, 0, 0))

        # Variable d'état
        self.macro = None
        self.categorie = None
        self.macro_edited = None

        self.ls = Listener()
        self.simulator: Simulator | None = None
        self.windows = None
        self.apps = get_taskbar_apps()
        self.monitors = list_monitors()

        self._event_scroll_area_isload_event_id = None

        self.loadEventScrollArea_uuid = None
        self._anim_signal.connect(self.launchEventAnim)
        self._launch_anim_signal.connect(lambda macro_id, index: self.setMacro(macro_id, max(0, (index or 0) - 10)) if self.macro != macro_id else None)
        self._event_scroll_area_isload.connect(lambda: None)

        # Affichage
        self.widget = QWidget()
        self.setCentralWidget(self.widget)
        self.main_layout = QHBoxLayout(self.widget)

        self.left_layout = QVBoxLayout()
        self.middle_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        self.main_layout.addLayout(self.left_layout, 0)
        self.main_layout.addLayout(self.middle_layout, 1)
        self.main_layout.addLayout(self.right_layout, 2)

        ## Left Zone
        # Ligne 1
        self.launch_button = QPushButton("lancer la macro", self)
        self.launch_button.clicked.connect(self.launchMacro)
        self.left_layout.addWidget(self.launch_button)

        # Ligne 2
        self.button = QPushButton("Enregistrer", self)
        self.button.clicked.connect(self.recordNewMacro)
        self.left_layout.addWidget(self.button)

        # Ligne 2 col 1
        self.save_widget_layout = QHBoxLayout()
        self.left_layout.addLayout(self.save_widget_layout)

        self.save_button = QPushButton("Sauvegarder", self)
        self.save_button.clicked.connect(self.saveMacro)
        self.save_button.hide()
        self.save_widget_layout.addWidget(self.save_button)

        # Ligne 2 col 2
        self.name_save = QLineEdit(self)
        self.name_save.hide()
        self.save_widget_layout.addWidget(self.name_save)

        # Ligne 2 col 3
        self.cancel_save = QPushButton("Annuler", self)
        self.cancel_save.setStyleSheet("background: rgb(200, 0, 0); border: 1px solid white; border-radius: 8px")
        self.cancel_save.clicked.connect(self.cancelMacro)
        self.cancel_save.hide()
        self.save_widget_layout.addWidget(self.cancel_save)

        # Ligne 3 col 1
        self.categ_widgets_layout = QHBoxLayout()
        self.left_layout.addLayout(self.categ_widgets_layout)

        self.add_categ_edit = QLineEdit(self)
        self.categ_widgets_layout.addWidget(self.add_categ_edit)

        # Ligne 3 col 2
        self.add_categ_btn = QPushButton("ajouter categ", self)
        self.add_categ_btn.clicked.connect(self.add_categ)
        self.categ_widgets_layout.addWidget(self.add_categ_btn)

        # Ligne 3 col 3
        self.delete_categ_btn = QPushButton("Retirer categ", self)
        self.delete_categ_btn.clicked.connect(self.deleteCateg)
        self.categ_widgets_layout.addWidget(self.delete_categ_btn)

        # Ligne 4 col 1
        self.macro_widgets_layout = QHBoxLayout()
        self.left_layout.addLayout(self.macro_widgets_layout)

        self.add_seq_edit = QLineEdit(self)
        self.macro_widgets_layout.addWidget(self.add_seq_edit)

        # Ligne 4 col 2
        self.add_seq_btn = QPushButton("Ajout macro", self)
        self.add_seq_btn.clicked.connect(self.addNewBlankMacro)
        self.macro_widgets_layout.addWidget(self.add_seq_btn)

        self.separator_1 = QFrame(self)
        self.separator_1.setFixedHeight(2)
        self.separator_1.setStyleSheet("border-top: 2px solid white")
        self.left_layout.addWidget(self.separator_1)

        # PosParams
        self.is_relative = QCheckBox("Relatif", self)
        self.left_layout.addWidget(self.is_relative)

        self.base = QComboBox(self)
        self.base.addItems(list(PosBase.__members__.keys()))

        monitors_names = self.get_monitors()

        self.base_name = QComboBox(self)
        self.base_name.addItems(monitors_names)
        self.pos_params.base_name = self.base_name.currentText()

        self.is_relative.checkStateChanged.connect(self.setPosParamsIsRelative)
        self.base_name.currentTextChanged.connect(self.setPosParamsBaseName)
        self.base.currentTextChanged.connect(self.setPosParamsBase)

        self.params_layout = QHBoxLayout()
        self.left_layout.addLayout(self.params_layout)

        self.params_layout.addWidget(self.base)
        self.params_layout.addWidget(self.base_name)

        self.left_layout.addStretch(1)
        ## Middle Zone
        self.macros_scroll_area = QScrollCategorie(self)
        self.loadMacroScrollArea()
        self.macros_scroll_area.setMinimumWidth(250)
        self.middle_layout.addWidget(self.macros_scroll_area, 1)

        # Right Zone
        self.event_scroll_area = QScroll(self)
        self.event_scroll_area.setMinimumWidth(250)

        self.pre_load__event_scroll_area = QScroll(self)
        self.pre_load__event_scroll_area.hide()
        self.right_layout.addWidget(self.event_scroll_area, 30)

    # Arrête correctement les prévisualisations en cours
    def closeEvent(self, event: QCloseEvent):
        qevent: EventItem = self.event_scroll_area.items.get(self.macro_edited)
        if qevent: qevent.removeEditMode()
        if self.simulator: self.simulator.stop()
        event.accept()

    # Edit Config
    def setPosParamsIsRelative(self, value):
        self.pos_params.is_relative = value

    def setPosParamsBase(self, value):
        self.pos_params.base = PosBase[value]
        self.base_name.clear()
        self.base_name.addItems({"WINDOWS": self.get_apps(), "SCREEN": self.get_monitors()}[value])

    def setPosParamsBaseName(self, value):
        self.pos_params.base_name = value

    def get_apps(self):
        self.apps = get_taskbar_apps()
        return [x.get("title") for x in self.apps]

    def get_monitors(self):
        self.monitors = list_monitors()
        return [x.get("Device") for x in self.monitors]

    # Manage Categories
    def add_categ(self):
        name = self.add_categ_edit.text()
        categ_id = database_manager.Categorie.add(name)[0]

        self.add_categ_edit.clear()
        self.loadMacroScrollArea()
        self.macros_scroll_area.setCurrentCateg(categ_id)

    def deleteCateg(self):
        categ_id = self.macros_scroll_area.categSlc
        database_manager.Categorie.delete(categ_id)
        self.macros_scroll_area.removeCateg(categ_id)

    # Manage Macros
    def addNewBlankMacro(self):
        name = self.add_seq_edit.text()
        if self.macros_scroll_area.categSlc is None:
            return
        macro_id = database_manager.Macro.add(name, self.macros_scroll_area.categSlc)[0]

        self.addMacroScrollAreaItem((macro_id, name))
        self.add_seq_edit.clear()

    def deleteMacro(self, macro):
        database_manager.Macro.delete(macro)
        self.macros_scroll_area.remove(macro)

    @qasync.asyncSlot()
    async def saveMacro(self):
        text = self.name_save.text()
        if not text:
            return
        self.button.show()
        self.save_button.hide()
        self.name_save.clear()
        self.name_save.hide()
        self.cancel_save.hide()
        macro_id = self.ls.save(text, self.macros_scroll_area.categSlc, database_manager)
        self.addMacroScrollAreaItem((macro_id, text))

    @qasync.asyncSlot()
    async def cancelMacro(self):
        self.button.show()
        self.save_button.hide()
        self.name_save.clear()
        self.name_save.hide()
        self.cancel_save.hide()

    # Set Etats
    @qasync.asyncSlot()
    async def setMacro(self, macro, start_index=0):
        self.macro = macro
        await self.loadEventScrollArea(start_index)

    @qasync.asyncSlot()
    async def setCategorie(self, categorie):
        self.categorie = categorie
        await self.loadEventScrollArea()

    # Manage Events
    async def adjusteScrollEditEvent(self, index, height):
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        value = (index + 1) * 36 + height - self.event_scroll_area.verticalScrollBar().value()
        scroll_value = self.event_scroll_area.verticalScrollBar().value()
        if value > self.event_scroll_area.height():
            self.event_scroll_area.verticalScrollBar().setValue(
                scroll_value + (value - self.event_scroll_area.height()))

    def saveEditedEvent(self, qevent: EventItem):
        qevent.config_item.event.update(database_manager)
        self.setMacro(self.macro)
        self.macro_edited = None

    def deleteEvent(self, _id):
        database_manager.Event.delete(_id)
        self.event_scroll_area.remove(_id)
        self.macro_edited = None

    @qasync.asyncSlot()
    async def addEvent(self, index: int, _id, macro_id):
        item = QNowEvent()
        item.setSaveCallback(lambda event: self.saveEvent(_id, macro_id, event))
        item.setCancelCallback(lambda: self.cancelAddEvent())
        item_value = self.event_scroll_area.insert(index, item, "edit")
        if item_value:
            await self.adjusteScrollEditEvent(index, item.height())

    def saveEvent(self, _id, macro_id, event: Event):
        position = database_manager.Position.getInsertPosition(_id, macro_id)
        event.save(database_manager, macro_id, position)
        self.setMacro(self.macro)

    def cancelAddEvent(self):
        self.event_scroll_area.remove("edit")

    @qasync.asyncSlot()
    async def editEvent(self, event_id, index):
        old_qevent = self.event_scroll_area.items.get(self.macro_edited)
        qevent: EventItem = self.event_scroll_area.items[event_id]
        assert isinstance(old_qevent, EventItem | None)
        assert isinstance(qevent, EventItem)

        if self.macro_edited == event_id:
            old_qevent.removeEditMode()
            self.macro_edited = None
            return
        if self.macro_edited is not None and old_qevent is not None:
            old_qevent.removeEditMode()

        qevent.setEditMode()
        await self.adjusteScrollEditEvent(index, qevent.height())
        self.macro_edited = event_id

    # Load Scroll AREA
    def loadMacroScrollArea(self):
        categories = database_manager.Categorie.getAlls()[1]

        for categ in categories:
            categ_id, categ_name = categ
            self.macros_scroll_area.addCateg(categ_id, categ_name)
            self.macros_scroll_area.setCurrentCateg(categ_id)
            self.macros_scroll_area.clear()

            for macro in database_manager.Macro.getMacroOfCategorie(categ_id)[1]:
                self.addMacroScrollAreaItem((macro[0], macro[1]))

        if categories:
            self.macros_scroll_area.setCurrentCateg(categories[0][0])

    def addMacroScrollAreaItem(self, macro: tuple):
        item = QFrame(self.macros_scroll_area)
        item.setFixedHeight(25)
        button = QPushButton(macro[1], item)
        button.clicked.connect(lambda _, fi=macro[0]: self.setMacro(fi))
        button.setGeometry(0, 0, 100, 27)

        delete_button = QPushButton("🗑️", item)
        delete_button.clicked.connect(lambda _, fi=macro[0]: self.deleteMacro(fi))
        delete_button.setGeometry(120, 0, 100, 27)
        self.macros_scroll_area.add(item, macro[0])

    @qasync.asyncSlot()
    async def loadEventScrollArea(self, start_index=0):
        self.event_scroll_area.clear()
        self.loadEventScrollArea_uuid = secrets.token_hex()
        uuid = self.loadEventScrollArea_uuid
        events: list[Event] = ListEvent(database_manager.Event.getEventOfMacro(self.macro)[1])
        button = QPushButton("➕")
        button.setFixedHeight(30)
        button.clicked.connect(lambda _: self.addEvent(0, None, self.macro))
        self.event_scroll_area.add(button, "button")

        for k, i in enumerate(events[start_index:]):
            k += 1
            item = EventItem(i)
            item.setEditCallback(lambda _, fi=i.id, fk=k: self.editEvent(fi, fk))
            item.setSaveCallback(lambda _, fi=item: self.saveEditedEvent(fi))
            item.setAddCallback(lambda _, fk=k, fi=i.id: self.addEvent(fk + 1, fi, self.macro))
            item.setDeleteCallback(lambda _, fi=i.id: self.deleteEvent(fi))
            if self.loadEventScrollArea_uuid != uuid:
                return
            self.event_scroll_area.add(item, i.id)
            await asyncio.sleep(0.001)
            self._event_scroll_area_isload.emit(datetime.datetime.now().timestamp())


    # Action Buttons
    @qasync.asyncSlot()
    async def recordNewMacro(self):
        self.button.setDisabled(True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.recordNewMacro2)
        self.button.setDisabled(False)

    def recordNewMacro2(self):
        self.ls.start(self.pos_params)
        self.ls.join()
        self.button.hide()
        self.save_button.show()
        self.name_save.show()
        self.cancel_save.show()

    @qasync.asyncSlot()
    async def launchMacro(self):
        if not self.macro:
            return
        self.launch_button.setDisabled(True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.launchMacro2)
        self.launch_button.setDisabled(False)

    def launchMacro2(self):
        self.event_scroll_area.verticalScrollBar().setDisabled(True)
        self.simulator = Simulator(self.macro)
        self.simulator.start_event = lambda x: [self._anim_signal.emit(x)]
        self.simulator.enter_launch_event = lambda x, index: [self._launch_anim_signal.emit(x, index)]
        self.simulator.run()
        self.event_scroll_area.verticalScrollBar().setDisabled(False)

    def launchEventAnim(self, x, delay=0):
        a: EventItem = self.event_scroll_area.items.get(x)
        if  a:
            a.loadAnim(delay)
            self.event_scroll_area.verticalScrollBar().setValue(self.event_scroll_area.index(x)*36 - self.event_scroll_area.height()//2)
            if self._event_scroll_area_isload_event_id == x:
                self._event_scroll_area_isload.disconnect()
                self._event_scroll_area_isload_event_id = None
        elif self._event_scroll_area_isload_event_id != x:
            self._event_scroll_area_isload_event_id = x
            self._event_scroll_area_isload.disconnect()
            self._event_scroll_area_isload.connect(lambda y: [self.launchEventAnim(x, round(datetime.datetime.now().timestamp() - y))])
            self._event_scroll_area_isload_event_id = None
