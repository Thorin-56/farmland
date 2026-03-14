import asyncio
import json
import sys

import qasync
from PySide6.QtWidgets import QMainWindow, QPushButton, QLineEdit, QFrame
from qasync import QEventLoop, QApplication

from Listerners.Event import ListEvent
from Listerners.Listener import Listener
from Listerners.Simulator import Simulator
from GuiObjects.QObjects import QScrollCategorie


class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Farmland")
        self.setGeometry(100, 100, 700, 500)

        self.ls = Listener()

        self.macro = None

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

        self.test_scroll = QScrollCategorie(self)
        self.test_scroll.setGeometry(350, 20, 300, 400)
        self.loadScroll()

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
                self.addItem(i)

        if list(file.get("seq").keys()):
            self.test_scroll.setCurrentCateg(list(file.get("seq").keys())[0])

    def addItem(self, key):
        item = QFrame(self.test_scroll)
        item.setFixedHeight(25)
        button = QPushButton(key, item)
        button.clicked.connect(lambda _, fi=key: self.setMacro(fi))
        button.setGeometry(0, 0, 100, 27)

        delete_button = QPushButton("🗑️", item)
        delete_button.clicked.connect(lambda _, fi=key: self.deleteMacro(fi))
        delete_button.setGeometry(120, 0, 100, 27)
        self.test_scroll.add(item, key)

    def setMacro(self, name):
        self.macro = name

    def deleteMacro(self, name):
        with open("point.json", "r") as file:
            file = json.load(file)

        file["seq"][self.test_scroll.categSlc].pop(name)
        with open("point.json", "w") as file2:
            json.dump(file, file2)
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
        json_events = file["seq"][self.test_scroll.categSlc][self.macro]
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
        self.addItem(text)

    @qasync.asyncSlot()
    async def cancelMacro(self):
        self.button.show()
        self.save_button.hide()
        self.name_save.clear()
        self.name_save.hide()
        self.cancel_save.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    windows = MainWindows()
    windows.show()

    with loop:
        loop.run_forever()
