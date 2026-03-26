import asyncio
import json
import sys

import qasync
from PySide6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFrame, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QDoubleSpinBox
from PySide6.QtCore import Qt
from qasync import QEventLoop, QApplication

from GuiObjects.QCustomObjects import QEvent, QNowEvent
from Listerners.Event import ListEvent, Event
from Listerners.Listener import Listener
from Listerners.Simulator import Simulator
from GuiObjects.QObjects import QScrollCategorie, QScroll
from config import FILE_PATH


class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Farmland")
        self.setGeometry(100, 100, 700, 500)

        self.ls = Listener()

        self.macro = None
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
        with open("point.json", "r") as file:
            file = json.load(file)

        file["seq"][name] = {}
        with open("point.json", "w") as file2:
            json.dump(file, file2)
        self.add_categ_edit.clear()
        self.loadScroll()
        self.test_scroll.setCurrentCateg(name)

    def deleteCateg(self):
        name = self.test_scroll.categSlc
        with open("point.json", "r") as file:
            file = json.load(file)
        assert isinstance(file, dict)
        if len(file["seq"].get(name)):
            print("ok")
            return
        file["seq"].pop(name)
        with open("point.json", "w") as file2:
            json.dump(file, file2)
        self.test_scroll.removeCateg(name)

    def loadScroll(self):
        with open("point.json", "r") as file:
            file = json.load(file)

        for categ in file.get("seq").keys():
            self.test_scroll.addCateg(categ)
            self.test_scroll.setCurrentCateg(categ)
            self.test_scroll.clear()
            keys = file.get("seq").get(categ).keys()

            for i in keys:
                self.addItem((categ, i))

        if list(file.get("seq").keys()):
            self.test_scroll.setCurrentCateg(list(file.get("seq").keys())[0])

    def addItem(self, macro: tuple):
        item = QFrame(self.test_scroll)
        item.setFixedHeight(25)
        button = QPushButton(macro[1], item)
        button.clicked.connect(lambda _, fi=macro: self.setMacro(fi))
        button.setGeometry(0, 0, 100, 27)

        delete_button = QPushButton("🗑️", item)
        delete_button.clicked.connect(lambda _, fi=macro: self.deleteMacro(fi))
        delete_button.setGeometry(120, 0, 100, 27)
        self.test_scroll.add(item, macro[1])

    def setMacro(self, macro):
        self.macro = macro
        self.loadEditMacro()

    def addMacro(self):
        name = self.add_seq_edit.text()
        if self.test_scroll.categSlc is None:
            return
        if self.file["seq"][self.test_scroll.categSlc].get(name) is not None:
            return
        file = self.file
        file["seq"][self.test_scroll.categSlc][name] = {}
        self.file = file

        self.addItem((self.test_scroll.categSlc, name))
        self.add_seq_edit.clear()

    def deleteMacro(self, macro):
        print(macro)
        categ, name = macro
        file = self.file
        file["seq"][categ].pop(name)
        self.file = file
        self.test_scroll.remove(name)

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
        with open("point.json", "r") as file:
            file = json.load(file)

        assert isinstance(file, dict)
        json_events = file["seq"][self.macro[0]][self.macro[1]]
        events = ListEvent(json_events)

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
        self.ls.save("point.json", ("seq", self.test_scroll.categSlc, text))
        self.addItem((self.test_scroll.categSlc, text))

    @qasync.asyncSlot()
    async def cancelMacro(self):
        self.button.show()
        self.save_button.hide()
        self.name_save.clear()
        self.name_save.hide()
        self.cancel_save.hide()

    def loadEditMacro(self):
        self.manage_macro.clear()
        events: list[Event] = ListEvent(self.file["seq"][self.macro[0]][self.macro[1]])
        for k, i in enumerate(events):

            item = QEvent(i)
            item.setEditCallback(lambda _, fk=k: self.editMacro(fk))
            item.setSaveCallback(lambda _, fk=k, fi=item: self.saveEditedMacro(fk, fi))
            item.setAddCallback(lambda _, fk=k: self.addEditedMacro(fk+1))

            self.manage_macro.add(item, k)

    def saveEditedMacro(self, index: int, qevent: QEvent):
        file = self.file
        file["seq"][self.macro[0]][self.macro[1]][index] = qevent.event_value.jsonify()
        self.file = file
        self.setMacro(self.macro)
        self.macro_edited = None

    def deleteEditedMacro(self, index: int):
        file = self.file
        file["seq"][self.macro[0]][self.macro[1]].pop(index)
        self.file = file
        self.setMacro(self.macro)
        self.macro_edited = None

    def addEditedMacro(self, index: int):
        item = QNowEvent()
        self.manage_macro.insert(index, item, "edit")

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


    @property
    def file(self):
        with open(FILE_PATH, "r") as file:
            file = json.load(file)
            assert isinstance(file, dict)
        return file

    @file.setter
    def file(self, value):
        assert isinstance(value, dict)
        with open(FILE_PATH, "w") as file:
            json.dump(value, file)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_loop = QEventLoop(app)
    asyncio.set_event_loop(main_loop)

    windows = MainWindows()
    windows.show()

    with main_loop:
        main_loop.run_forever()
