import pynput
import qasync
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button
from shiboken6.Shiboken import Object


class QScroll(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.items: dict[str, QWidget] = {}

        self.main_widget = QWidget()
        self.vbox = QVBoxLayout()
        self.main_widget.setLayout(self.vbox)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setWidgetResizable(True)
        self.setWidget(self.main_widget)

        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

    def add(self, _object, name):
        if name in list(self.items.keys()):
            return
        self.vbox.addWidget(_object)
        self.items.update({name: _object})


    def insert(self, index, _object, name):
        if name in list(self.items.keys()):
            return
        self.vbox.insertWidget(index, _object)
        self.items.update({name: _object})

    def remove(self, name):
        self.vbox.removeWidget(self.items[name])
        self.items[name].deleteLater()
        self.items.pop(name)

    def clear(self):
        for i in list(self.items.keys()):
            self.remove(i)


class QHorizontalScroll(QScroll):
    def wheelEvent(self, event):
        scrollbar = self.horizontalScrollBar()
        scrollbar.setValue(scrollbar.value() - event.angleDelta().y())
        event.accept()

class QScrollCategorie(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.headers = QHorizontalScroll(self)
        self.headers_height = 30
        self.headers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.headers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.headers.vbox.setContentsMargins(0, 0, 0, 0)
        self.headers.vbox.setDirection(QVBoxLayout.Direction.LeftToRight)
        self.headers.vbox.setSpacing(0)
        self.headers.setGeometry(0, 0, self.width(), self.headers_height)

        self.scroll: QScroll | None = None

        self.categ: dict[str, dict[str, QWidget]] = {}
        self.categ_h = {}
        self.categSlc = None

    def setCurrentCateg(self, _id):
        if self.categSlc:
            self.categ_h[self.categSlc]["button"].setStyleSheet("color: white")
            self.scroll.hide()

        self.categSlc = _id
        self.scroll = self.categ[_id]["scroll"]
        self.scroll.setGeometry(0, self.headers_height, self.width(), self.height() - self.headers_height)
        self.scroll.show()

        self.categ_h[_id]["button"].setStyleSheet("color: red")

    def addCateg(self, _id, name):
        if _id in self.categ.keys():
            return

        scroll = QScroll(self)
        scroll.hide()
        self.categ.update({_id: {"name": name, "scroll": scroll}})
        button = QPushButton(name)
        button.setFixedSize(100, self.headers_height - 4)
        button.clicked.connect(lambda _, fi=_id: self.setCurrentCateg(fi))
        self.categ_h.update({_id: {"name": name, "button": button}})
        self.headers.add(button, _id)
        if self.categSlc is None:
            self.setCurrentCateg(_id)

    def removeCateg(self, name):
        if name not in self.categ.keys():
            return
        self.categ[name]["scroll"].deleteLater()
        self.categ_h[name]["button"].deleteLater()
        self.categ.pop(name)
        self.categ_h.pop(name)
        if self.categSlc == name:
            self.categSlc = None
            if self.categ:
                self.setCurrentCateg(list(self.categ.keys())[0])
            else:
                self.setCurrentCateg(None)

    def clear_header(self):
        self.headers.clear()

    def add(self, *args):
        self.scroll.add(*args)

    def remove(self, *args):
        self.scroll.remove(*args)

    def clear(self):
        self.scroll.clear()
    
    def setGeometry(self, *args):
        x, y, w, h = args
        super().setGeometry(x, y, w, h)
        
        self.headers.setGeometry(0, 0, self.width(), self.headers_height)
        if self.scroll:
            self.scroll.setGeometry(0, self.headers_height, self.width(), self.height() - self.headers_height)


class QBindKeyButton(QPushButton):
    _keyPressed = Signal(object)
    changed = Signal(object)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setText(" ? ")
        self.__key = None
        self.ls = None

        self._keyPressed.connect(self._onKeyPressed)
        self.clicked.connect(self.getKey)
        self.destroyed.connect(lambda: self.stopOnDestroy(None))

    @staticmethod
    def stopOnDestroy(ls):
        if ls is None:
            return
        else:
            ls.stop()

    @qasync.asyncSlot()
    async def getKey(self):
        self._stopListener()
        self.setText("...")
        self.clicked.disconnect()
        self.ls = pynput.keyboard.Listener(on_press=self._getKey)
        self.destroyed.disconnect()
        self.destroyed.connect(lambda _, ls1=self.ls: self.stopOnDestroy(ls1))
        self.ls.start()

    def _getKey(self, key: Key | KeyCode | None):
        try:
            self._keyPressed.emit(key)
        except RuntimeError:
            pass
        self.clicked.connect(self.getKey)
        return False

    def _onKeyPressed(self, key):
        self.__key = key
        self.setText(str(key))
        self.changed.emit(key)
        self._stopListener()

    def _stopListener(self):
        if self.ls is not None:
            self.ls.stop()
            self.ls = None

    @property
    def key(self):
        return self.__key


class QBindMouseButton(QPushButton):
    _btnPressed = Signal(object)
    changed = Signal(object)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setText(" ? ")
        self.__btn = None
        self.ls = None

        self._btnPressed.connect(self._onBtnPressed)
        self.clicked.connect(self.getBtn)
        self.destroyed.connect(lambda: self.stopOnDestroy(None))

    @staticmethod
    def stopOnDestroy(ls):
        if ls is None:
            return
        else:
            ls.stop()

    @qasync.asyncSlot()
    async def getBtn(self):
        self._stopListener()
        self.setText("...")
        self.clicked.disconnect()
        self.ls = pynput.mouse.Listener(on_click=self._getBtn)
        self.destroyed.disconnect()
        self.destroyed.connect(lambda _, ls1=self.ls: self.stopOnDestroy(ls1))
        self.ls.start()

    def _getBtn(self, _, __, btn: Button):
        try:
            self._btnPressed.emit(btn)
        except RuntimeError:
            pass
        self.clicked.connect(self.getBtn)
        return False

    def _onBtnPressed(self, btn: Button):
        self.__btn = btn
        self.setText(btn.name)
        self.changed.emit(btn)
        self._stopListener()

    def _stopListener(self):
        if self.ls is not None:
            self.ls.stop()
            self.ls = None

    @property
    def btn(self):
        return self.__btn

