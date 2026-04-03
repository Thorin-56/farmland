import asyncio
import sys

import qasync
from PySide6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFrame
from qasync import QEventLoop, QApplication

from VARS import database_manager
from GuiObjects.QCustomObjects import QEvent, QNowEvent
from Listerners.Event import ListEvent, Event
from Listerners.Listener import Listener
from Listerners.Simulator import Simulator
from GuiObjects.QObjects import QScrollCategorie, QScroll


class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Farmland")
        self.setGeometry(100, 100, 700, 500)

        self.ls = Listener()

        self.macro = None
        self.categorie = None
        self.macro_edited = None

        self.button = QPushButton("Enregistrer", self)
        self.button.clicked.connect(self.test)
        self.button.setGeometry(10, 45, 100, 30)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.saveMacro)
        self.save_button.setGeometry(10, 45, 100, 30)
        self.save_button.hide()

        self.name_save = QLineEdit(self)
        self.name_save.setGeometry(10, 80, 100, 30)
        self.name_save.hide()

        self.cancel_save = QPushButton("Annuler", self)
        self.cancel_save.setGeometry(10, 115, 100, 30)
        self.cancel_save.setStyleSheet("background: rgb(200, 0, 0); border: 1px solid white; border-radius: 8px")
        self.cancel_save.clicked.connect(self.cancelMacro)
        self.cancel_save.hide()

        self.launch_button = QPushButton("launch", self)
        self.launch_button.clicked.connect(self.test3)
        self.launch_button.setGeometry(10, 10, 100, 30)

        self.delete_categ_btn = QPushButton("Retirer categ", self)
        self.delete_categ_btn.setGeometry(110, 10, 100, 30)
        self.delete_categ_btn.clicked.connect(self.deleteCateg)

        self.add_categ_btn = QPushButton("ajouter categ", self)
        self.add_categ_btn.setGeometry(110, 45, 100, 30)
        self.add_categ_btn.clicked.connect(self.add_categ)

        self.add_categ_edit = QLineEdit(self)
        self.add_categ_edit.setGeometry(110, 80, 100, 30)

        self.add_seq_btn = QPushButton("Ajout macro", self)
        self.add_seq_btn.clicked.connect(self.addMacro)
        self.add_seq_btn.setGeometry(210, 10, 100, 30)

        self.add_seq_edit = QLineEdit(self)
        self.add_seq_edit.setGeometry(210, 45, 100, 30)

        self.test_scroll = QScrollCategorie(self)
        self.test_scroll.setGeometry(10, 150, 300, 300)
        self.loadScroll()

        self.manage_macro = QScroll(self)
        self.manage_macro.setGeometry(310, 10, 400, 440)

    def add_categ(self):
        name = self.add_categ_edit.text()
        categ_id = database_manager.addCategorie(name)[0]

        self.add_categ_edit.clear()
        self.loadScroll()
        self.test_scroll.setCurrentCateg(categ_id)

    def deleteCateg(self):
        categ_id = self.test_scroll.categSlc
        database_manager.deleteCategories(categ_id)
        self.test_scroll.removeCateg(categ_id)

    def loadScroll(self):
        categories = database_manager.getCategories()[1]

        for categ in categories:
            categ_id, categ_name = categ
            self.test_scroll.addCateg(categ_id, categ_name)
            self.test_scroll.setCurrentCateg(categ_id)
            self.test_scroll.clear()

            for macro in database_manager.getMacroOfCategorie(categ_id)[1]:
                self.addItem((macro[0], macro[1]))

        if categories:
            self.test_scroll.setCurrentCateg(categories[0][0])

    def addItem(self, macro: tuple):
        item = QFrame(self.test_scroll)
        item.setFixedHeight(25)
        button = QPushButton(macro[1], item)
        button.clicked.connect(lambda _, fi=macro[0]: self.setMacro(fi))
        button.setGeometry(0, 0, 100, 27)

        delete_button = QPushButton("🗑️", item)
        delete_button.clicked.connect(lambda _, fi=macro[0]: self.deleteMacro(fi))
        delete_button.setGeometry(120, 0, 100, 27)
        self.test_scroll.add(item, macro[0])

    def setMacro(self, macro):
        self.macro = macro
        self.loadEditMacro()

    def setCategorie(self, categorie):
        self.categorie = categorie
        self.loadEditMacro()

    def addMacro(self):
        name = self.add_seq_edit.text()
        if self.test_scroll.categSlc is None:
            return
        macro_id = database_manager.addMacro(name, self.test_scroll.categSlc)[0]

        self.addItem((macro_id, name))
        self.add_seq_edit.clear()

    def deleteMacro(self, macro):
        database_manager.deleteMacro(macro)
        self.test_scroll.remove(macro)

    @qasync.asyncSlot()
    async def test(self):
        self.button.setDisabled(True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.test2)
        self.button.setDisabled(False)

    def test2(self):
        self.ls.start()
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
        macro_id = self.ls.save(text, self.test_scroll.categSlc, database_manager)
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
        qevent = self.manage_macro.items[index]
        assert isinstance(old_qevent, QEvent | None)
        assert isinstance(qevent, QEvent)

        if self.macro_edited == index:
            old_qevent.setFixedHeight(30)
            old_qevent.config_area.clear()
            self.macro_edited = None
            return
        if self.macro_edited is not None:
            old_qevent.setFixedHeight(30)
            old_qevent.config_area.clear()

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
