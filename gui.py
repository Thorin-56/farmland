import asyncio
import sys
import time

import qasync
from PySide6.QtCore import QPoint
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFrame, QCheckBox, QComboBox, QWidget, QVBoxLayout, \
    QLabel
from qasync import QEventLoop, QApplication

from Types.app_types import PosParams
from VARS import database_manager
from Types.GuiObjects.QCustomObjects import QEvent, QNowEvent
from Types.Listerners.Event import ListEvent, Event, PosBase, EventClick, Pos
from Types.Listerners.Listener import Listener
from Types.Listerners.Simulator import Simulator
from Types.GuiObjects.QObjects import QScrollCategorie, QScroll
from windows.list_windows import get_taskbar_apps
from windows.list_monitors import list_monitors
from windows.previewOverlay import Window, delete_border
from windows.windows import get_windows_pos


class AnotherWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Another Window")
        layout.addWidget(self.label)
        self.setLayout(layout)

class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoFarm")
        self.setGeometry(100, 100, 1100, 750)
        self.setFixedSize(1100, 750)

        self.pos_params = PosParams(False, PosBase.SCREEN, base_name=None, margins=(0, 0, 0, 0))

        self.ls = Listener()

        self.macro = None
        self.categorie = None
        self.macro_edited = None

        ## Left Zone
        # Ligne 1
        self.launch_button = QPushButton("lancer la macro", self)
        self.launch_button.clicked.connect(self.test3)
        self.launch_button.setGeometry(10, 10, 300, 30)

        # Ligne 2
        self.button = QPushButton("Enregistrer", self)
        self.button.clicked.connect(self.start_record)
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
        self.add_seq_btn.clicked.connect(self.addMacro)
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

        self.apps = get_taskbar_apps()

        self.monitors = list_monitors()
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
        self.loadScroll()

        # Right Zone
        self.manage_macro = QScroll(self)
        self.manage_macro.setGeometry(600, 10, 500, 700)

        self.windows = None


    def closeEvent(self, event: QCloseEvent):
        qevent: QEvent = self.manage_macro.items.get(self.macro_edited)
        qevent.removeEditMode()
        event.accept()

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

    def add_categ(self):
        name = self.add_categ_edit.text()
        categ_id = database_manager.addCategorie(name)[0]

        self.add_categ_edit.clear()
        self.loadScroll()
        self.macros_scroll_area.setCurrentCateg(categ_id)

    def deleteCateg(self):
        categ_id = self.macros_scroll_area.categSlc
        database_manager.deleteCategories(categ_id)
        self.macros_scroll_area.removeCateg(categ_id)

    def loadScroll(self):
        categories = database_manager.getCategories()[1]

        for categ in categories:
            categ_id, categ_name = categ
            self.macros_scroll_area.addCateg(categ_id, categ_name)
            self.macros_scroll_area.setCurrentCateg(categ_id)
            self.macros_scroll_area.clear()

            for macro in database_manager.getMacroOfCategorie(categ_id)[1]:
                self.addItem((macro[0], macro[1]))

        if categories:
            self.macros_scroll_area.setCurrentCateg(categories[0][0])

    def addItem(self, macro: tuple):
        item = QFrame(self.macros_scroll_area)
        item.setFixedHeight(25)
        button = QPushButton(macro[1], item)
        button.clicked.connect(lambda _, fi=macro[0]: self.setMacro(fi))
        button.setGeometry(0, 0, 100, 27)

        delete_button = QPushButton("🗑️", item)
        delete_button.clicked.connect(lambda _, fi=macro[0]: self.deleteMacro(fi))
        delete_button.setGeometry(120, 0, 100, 27)
        self.macros_scroll_area.add(item, macro[0])

    def setMacro(self, macro):
        self.macro = macro
        self.loadEditMacro()

    def setCategorie(self, categorie):
        self.categorie = categorie
        self.loadEditMacro()

    def addMacro(self):
        name = self.add_seq_edit.text()
        if self.macros_scroll_area.categSlc is None:
            return
        macro_id = database_manager.addMacro(name, self.macros_scroll_area.categSlc)[0]

        self.addItem((macro_id, name))
        self.add_seq_edit.clear()

    def deleteMacro(self, macro):
        database_manager.deleteMacro(macro)
        self.macros_scroll_area.remove(macro)

    @qasync.asyncSlot()
    async def start_record(self):
        self.button.setDisabled(True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.start_record2)
        self.button.setDisabled(False)

    def start_record2(self):
        self.ls.start(self.pos_params)
        self.ls.join()
        self.button.hide()
        self.save_button.show()
        self.name_save.show()
        self.cancel_save.show()

    @qasync.asyncSlot()
    async def test3(self):
        if not self.macro:
            return
        self.launch_button.setDisabled(True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.test4)
        self.launch_button.setDisabled(False)

    def test4(self):
        events = database_manager.getEventOfMacro(self.macro)[1]

        events = ListEvent(events)

        simulator = Simulator(events)
        simulator.run()

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
        self.addItem((macro_id, text))

    @qasync.asyncSlot()
    async def cancelMacro(self):
        self.button.show()
        self.save_button.hide()
        self.name_save.clear()
        self.name_save.hide()
        self.cancel_save.hide()

    def loadEditMacro(self):
        self.manage_macro.clear()
        events: list[Event] = ListEvent(database_manager.getEventOfMacro(self.macro)[1])
        button = QPushButton("➕")
        button.setFixedHeight(30)
        button.clicked.connect(lambda _: self.addEditedMacro(0, None, self.macro))
        self.manage_macro.add(button, "buton")

        for k, i in enumerate(events):
            k += 1
            item = QEvent(i)
            item.setEditCallback(lambda _, fk=k: self.editMacro(fk))
            item.setSaveCallback(lambda _, fi=item: self.saveEditedMacro(fi))
            item.setAddCallback(lambda _, fk=k, fi=i.id: self.addEditedMacro(fk+1, fi, self.macro))
            item.setDeleteCallback(lambda _, fi=i.id, fk=k: self.deleteEditedMacro(fi, fk))

            self.manage_macro.add(item, k)

    def saveEditedMacro(self, qevent: QEvent):
        _, time, data = qevent.event_value.jsonify()
        if qevent.event_value.type == "click":
            _position: Pos = data.pop("pos")
            base, windows_name, x_pourcent_width, x_pourcent_height, x_value, y_pourcent_width, y_pourcent_height, y_value, margins = _position.jsonify()
            print(margins, type(margins))
            database_manager.updatePosition(
                qevent.event_value.id,
                {"x_value": x_value, "y_value": y_value,
                 "x_pourcent_width": x_pourcent_width, "y_pourcent_width": y_pourcent_width,
                 "x_pourcent_height": x_pourcent_height, "y_pourcent_height": y_pourcent_height, "margins": margins
                 })
        database_manager.updateEvent(qevent.event_value.id, {"time": time, "data": data})
        self.setMacro(self.macro)
        self.macro_edited = None

    def deleteEditedMacro(self, _id, index: int):
        database_manager.deleteEvent(_id)
        self.manage_macro.remove(index)
        self.setMacro(self.macro)
        self.macro_edited = None

    def addEditedMacro(self, index: int, _id, macro_id):
        item = QNowEvent()
        item.setSaveCallback(lambda event: self.saveEvent(_id, macro_id, event))
        item.setCancelCallback(lambda: self.cancelAddEvent(item))
        self.manage_macro.insert(index, item, "edit")

    def saveEvent(self, _id, macro_id, event: Event):
        e_type, e_time, data = event.jsonify()
        data = str(data)
        database_manager.insertEvent(_id, e_type, e_time, data, macro_id)
        self.setMacro(self.macro)

    def cancelAddEvent(self, item: QNowEvent):
        self.manage_macro.remove("edit")

    def editMacro(self, index):
        old_qevent = self.manage_macro.items.get(self.macro_edited)
        qevent: QEvent = self.manage_macro.items[index]
        assert isinstance(old_qevent, QEvent | None)
        assert isinstance(qevent, QEvent)

        if self.macro_edited == index:
            old_qevent.removeEditMode()
            self.macro_edited = None
            return
        if self.macro_edited is not None and old_qevent is not None:
            old_qevent.removeEditMode()

        qevent.setEditMode()
        self.macro_edited = index

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_loop = QEventLoop(app)
    asyncio.set_event_loop(main_loop)

    windows = MainWindows()
    windows.show()

    with main_loop:
        main_loop.run_forever()
