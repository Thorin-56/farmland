import asyncio
import secrets

import qasync
from PySide6.QtCore import Signal, QRect
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFrame, QCheckBox, QComboBox, QWidget

from Types.GuiObjects.QCustomObjects import EventItem, QNowEvent
from Types.GuiObjects.QObjects import QScrollCategorie, QScroll
from Types.Listerners.Event import ListEvent, Event, PosBase, Pos, EventClick
from Types.Listerners.Listener import Listener
from Types.Listerners.Simulator import Simulator
from Types.app_types import PosParams
from VARS import database_manager
from windows.list_monitors import list_monitors
from windows.list_windows import get_taskbar_apps


class MainWindows(QMainWindow):
    _anim_signal = Signal(object)
    _launch_anim_signal = Signal(object)
    _preload_signal = Signal(object)
    _preload_finish_signal = Signal(object)
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoFarm")
        self.setGeometry(100, 100, 1100, 750)
        self.setFixedSize(1100, 750)

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

        self.loadEventScrollArea_uuid = None
        self._anim_signal.connect(self.test)
        self._launch_anim_signal.connect(self.change_event)
        self._preload_signal.connect(self.preload_event_area)

        ## Left Zone
        # Ligne 1
        self.launch_button = QPushButton("lancer la macro", self)
        self.launch_button.clicked.connect(self.launchMacro)
        self.launch_button.setGeometry(10, 10, 300, 30)

        # Ligne 2
        self.button = QPushButton("Enregistrer", self)
        self.button.clicked.connect(self.recordNewMacro)
        self.button.setGeometry(10, 45, 300, 30)

        # Ligne 2 col 1
        self.save_button = QPushButton("Sauvegarder", self)
        self.save_button.clicked.connect(self.saveMacro)
        self.save_button.setGeometry(10, 45, 100, 30)
        self.save_button.hide()

        # Ligne 2 col 2
        self.name_save = QLineEdit(self)
        self.name_save.setGeometry(110, 45, 100, 30)
        self.name_save.hide()

        # Ligne 2 col 3
        self.cancel_save = QPushButton("Annuler", self)
        self.cancel_save.setGeometry(210, 45, 100, 30)
        self.cancel_save.setStyleSheet("background: rgb(200, 0, 0); border: 1px solid white; border-radius: 8px")
        self.cancel_save.clicked.connect(self.cancelMacro)
        self.cancel_save.hide()

        # Ligne 3 col 1
        self.add_categ_edit = QLineEdit(self)
        self.add_categ_edit.setGeometry(10, 80, 100, 30)

        # Ligne 3 col 2
        self.add_categ_btn = QPushButton("ajouter categ", self)
        self.add_categ_btn.setGeometry(110, 80, 100, 30)
        self.add_categ_btn.clicked.connect(self.add_categ)

        # Ligne 3 col 3
        self.delete_categ_btn = QPushButton("Retirer categ", self)
        self.delete_categ_btn.setGeometry(210, 80, 100, 30)
        self.delete_categ_btn.clicked.connect(self.deleteCateg)

        # Ligne 4 col 1
        self.add_seq_edit = QLineEdit(self)
        self.add_seq_edit.setGeometry(10, 115, 100, 30)

        # Ligne 4 col 2
        self.add_seq_btn = QPushButton("Ajout macro", self)
        self.add_seq_btn.clicked.connect(self.addNewBlankMacro)
        self.add_seq_btn.setGeometry(110, 115, 100, 30)

        self.separator_1 = QFrame(self)
        self.separator_1.setGeometry(10, 165, 300, 1)
        self.separator_1.setStyleSheet("border-top: 2px solid white")

        # PosParams
        self.is_relative = QCheckBox("Relatif", self)
        self.is_relative.setGeometry(10, 185, 100, 30)

        self.base = QComboBox(self)
        self.base.addItems(PosBase.__members__.keys())
        self.base.setGeometry(10, 220, 100, 30)

        monitors_names = self.get_monitors()

        self.base_name = QComboBox(self)
        self.base_name.addItems(monitors_names)
        self.base_name.setGeometry(110, 220, 200, 30)
        self.pos_params.base_name = self.base_name.currentText()

        self.is_relative.checkStateChanged.connect(self.setPosParamsIsRelative)
        self.base_name.currentTextChanged.connect(self.setPosParamsBaseName)
        self.base.currentTextChanged.connect(self.setPosParamsBase)

        ## Middle Zone
        self.macros_scroll_area = QScrollCategorie(self)
        self.macros_scroll_area.setGeometry(325, 10, 275, 700)
        self.loadMacroScrollArea()

        # Right Zone
        self.base_geo = QRect(600, 10, 500, 700)
        self.event_scroll_area = QScroll(self)
        self.event_scroll_area.setGeometry(self.base_geo)

        self.pre_load__event_scroll_area = QScroll(self)
        self.pre_load__event_scroll_area.hide()

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
        categ_id = database_manager.addCategorie(name)[0]

        self.add_categ_edit.clear()
        self.loadMacroScrollArea()
        self.macros_scroll_area.setCurrentCateg(categ_id)

    def deleteCateg(self):
        categ_id = self.macros_scroll_area.categSlc
        database_manager.deleteCategories(categ_id)
        self.macros_scroll_area.removeCateg(categ_id)

    # Manage Macros
    def addNewBlankMacro(self):
        name = self.add_seq_edit.text()
        if self.macros_scroll_area.categSlc is None:
            return
        macro_id = database_manager.addMacro(name, self.macros_scroll_area.categSlc)[0]

        self.addMacroSrollAreaItem((macro_id, name))
        self.add_seq_edit.clear()

    def deleteMacro(self, macro):
        database_manager.deleteMacro(macro)
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
        self.addMacroSrollAreaItem((macro_id, text))

    @qasync.asyncSlot()
    async def cancelMacro(self):
        self.button.show()
        self.save_button.hide()
        self.name_save.clear()
        self.name_save.hide()
        self.cancel_save.hide()

    # Set Etats
    @qasync.asyncSlot()
    async def setMacro(self, macro):
        self.macro = macro
        await self.loadEventScrollArea()

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
        _, time, data = qevent.config_item.event.jsonify()
        if qevent.config_item.event.type == "click":
            base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, margins = qevent.config_item.event.pos.jsonify()
            database_manager.updatePosition(
                qevent.config_item.event.id,
                {"x_value": x_value, "y_value": y_value,
                 "x_pourcent_width": x_pourcent_width, "y_pourcent_width": y_pourcent_width,
                 "x_pourcent_height": x_pourcent_height, "y_pourcent_height": y_pourcent_height, "margins": margins
                 })
        database_manager.updateEvent(qevent.config_item.event.id, {"time": time, "data": data})
        self.setMacro(self.macro)
        self.macro_edited = None

    def deleteEvent(self, _id):
        database_manager.deleteEvent(_id)
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
        e_type, e_time, data = event.jsonify()
        position: Pos = event.pos if isinstance(event, EventClick) else None
        event_id = database_manager.insertEvent(_id, e_type, e_time, data, macro_id)[0]
        if position:
            database_manager.addPosition(*position.jsonify(), event_id)
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
        categories = database_manager.getCategories()[1]

        for categ in categories:
            categ_id, categ_name = categ
            self.macros_scroll_area.addCateg(categ_id, categ_name)
            self.macros_scroll_area.setCurrentCateg(categ_id)
            self.macros_scroll_area.clear()

            for macro in database_manager.getMacroOfCategorie(categ_id)[1]:
                self.addMacroSrollAreaItem((macro[0], macro[1]))

        if categories:
            self.macros_scroll_area.setCurrentCateg(categories[0][0])

    def addMacroSrollAreaItem(self, macro: tuple):
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
    async def loadEventScrollArea(self):
        self.event_scroll_area.clear()
        self.loadEventScrollArea_uuid = secrets.token_hex()
        uuid = self.loadEventScrollArea_uuid
        events: list[Event] = ListEvent(database_manager.getEventOfMacro(self.macro)[1])
        button = QPushButton("➕")
        button.setFixedHeight(30)
        button.clicked.connect(lambda _: self.addEvent(0, None, self.macro))
        self.event_scroll_area.add(button, "button")

        for k, i in enumerate(events):
            k += 1
            item = EventItem(i)
            item.setEditCallback(lambda _, fi=i.id, fk=k: self.editEvent(fi, fk))
            item.setSaveCallback(lambda _, fi=item: self.saveEditedEvent(fi))
            item.setAddCallback(lambda _, fk=k, fi=i.id: self.addEvent(fk + 1, fi, self.macro))
            item.setDeleteCallback(lambda _, fi=i.id: self.deleteEvent(fi))
            if self.loadEventScrollArea_uuid != uuid:
                return
            self.event_scroll_area.add(item, i.id)
            await asyncio.sleep(0.0)

    @qasync.asyncSlot()
    async def loadPreLoadEventScrollArea(self, macro_id):
        self.pre_load__event_scroll_area.clear()
        self.loadEventScrollArea_uuid = secrets.token_hex()
        uuid = self.loadEventScrollArea_uuid
        events: list[Event] = ListEvent(database_manager.getEventOfMacro(macro_id)[1])
        button = QPushButton("➕")
        button.setFixedHeight(30)
        button.clicked.connect(lambda _: self.addEvent(0, None, macro_id))
        self.pre_load__event_scroll_area.add(button, "button")

        for k, i in enumerate(events):
            k += 1
            item = EventItem(i)
            item.setEditCallback(lambda _, fi=i.id, fk=k: self.editEvent(fi, fk))
            item.setSaveCallback(lambda _, fi=item: self.saveEditedEvent(fi))
            item.setAddCallback(lambda _, fk=k, fi=i.id: self.addEvent(fk + 1, fi, macro_id))
            item.setDeleteCallback(lambda _, fi=i.id: self.deleteEvent(fi))
            if self.loadEventScrollArea_uuid != uuid:
                return
            self.pre_load__event_scroll_area.add(item, i.id)
            await asyncio.sleep(0.0)
        button_finish = QPushButton("➕")
        button_finish.setFixedHeight(30)
        button_finish.clicked.connect(lambda _: None)
        self.pre_load__event_scroll_area.add(QWidget(), "finish")
        self._preload_finish_signal.emit(macro_id)

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
        self.simulator.enter_launch_event = lambda x: [self._launch_anim_signal.emit(x)]
        self.simulator.preload_event = lambda x: [self._preload_signal.emit(x)]
        self.simulator.run()
        self.event_scroll_area.verticalScrollBar().setDisabled(False)

    def test(self, x):
        a: EventItem = self.event_scroll_area.items.get(x)
        if  a:
            a.loadAnim()
            self.event_scroll_area.verticalScrollBar().setValue(self.event_scroll_area.index(x)*36 - self.event_scroll_area.height()//2)

    def change_event(self, macro_id):
        if self.macro != macro_id:
            if self.pre_load__event_scroll_area.items.get("finish"):
                self.change_event_finish(macro_id)
            else:
                self._preload_finish_signal.connect(self.change_event_finish)

    def change_event_finish(self, macro_id):
        last = self.event_scroll_area
        self.event_scroll_area = self.pre_load__event_scroll_area
        last.deleteLater()
        self.event_scroll_area.setGeometry(self.base_geo)
        self.event_scroll_area.show()
        self.macro = macro_id
        self.pre_load__event_scroll_area = QScroll(self)
        self.pre_load__event_scroll_area.setGeometry(self.base_geo)

    def preload_event_area(self, macro_id):
        self.loadPreLoadEventScrollArea(macro_id)
