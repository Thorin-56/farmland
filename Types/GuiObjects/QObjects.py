from abc import ABCMeta, ABC, abstractmethod

import pynput
import qasync
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QPushButton, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt, Signal, QSize, QObject
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button

class CompactSpinBox(QSpinBox):
    def sizeHint(self):
        sh = super().sizeHint()
        return QSize(sh.width() - 25, sh.height())

class CompactDoubleSpinBox(QDoubleSpinBox):
    roundedValueChanged = Signal(float)
    def sizeHint(self):
        sh = super().sizeHint()
        return QSize(sh.width() - 25, sh.height())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        super().valueChanged.connect(lambda v: self.roundedValueChanged.emit(round(v, self.decimals())))

class QScroll(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.items: dict[str, QWidget] = {}
        self.items_list = []

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
        self.items_list.append(name)

    def insert(self, index, _object, name):
        if name in list(self.items.keys()):
            return False
        self.vbox.insertWidget(index, _object)
        self.items.update({name: _object})
        self.items_list.insert(index, name)
        return True

    def remove(self, name):
        self.vbox.removeWidget(self.items[name])
        self.items.pop(name).deleteLater()
        self.items_list.remove(name)

    def index(self, name):
        names = list(self.items.keys())
        if name not in names:
            return None
        return names.index(name)

    def clear(self):
        for i in list(self.items.keys()):
            self.remove(i)

    def keyPressEvent(self, event):
        pass


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
        self.categ_h: dict[str, dict[str, QWidget]] = {}
        self.categSlc = None

    def setCurrentCateg(self, _id):
        if self.categSlc:
            self.categ_h[self.categSlc]["button"].setStyleSheet("color: white")
            self.scroll.hide()

        self.categSlc = _id
        if self.categSlc is None:
            return
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

class QABCMeta(type(QObject), ABCMeta):
    pass

class BaseBindButton(QPushButton, ABC, metaclass=QABCMeta):
    valueSet = Signal(object)
    changed = Signal(object)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setText("?")

        self.__value = None
        self.__ls = None

        self.clicked.connect(self.launchListener)
        self.valueSet.connect(self.getValue)

    @qasync.asyncSlot()
    async def launchListener(self):
        self.setText("...")
        self.clicked.disconnect()
        self.destroyed.disconnect()
        self.destroyed.connect(lambda _, ls1=self.ls: self.stopListener(ls1))
        self.startListener()

    def getValue(self, *args, **kwargs):
        self.value = self.processValue(*args, **kwargs)
        self.changed.emit(self.value)
        self.clicked.connect(self.launchListener)
        self.stopListener(self.ls)

    def processValue(self, *args, **kwargs):
        value = args
        self.setText(value)
        return value

    @abstractmethod
    def startListener(self):
        pass

    @abstractmethod
    def stopListener(self, listener):
        pass

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value
        pass

    @property
    def ls(self):
        return self.__ls

    @ls.setter
    def ls(self, ls):
        self.__ls = ls
        self.destroyed.disconnect()
        self.destroyed.connect(lambda: self.stopListener(self.ls))

    def setValue(self, value):
        self.value = value
        self.setText(str(value))


class BindKeyButton(BaseBindButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def stopListener(self, listener: pynput.keyboard.Listener | None):
        if listener is not None:
            listener.stop()
        self.ls = None

    def startListener(self):
        self.ls = pynput.keyboard.Listener(on_press=self.getValue)
        self.ls.start()

    def processValue(self, value: Key | KeyCode, _):
        if isinstance(value, Key):
            self.setText(value.name)
        else:
            self.setText(value.char)
        return value


class BindMouseButton(BaseBindButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def stopListener(self, listener: pynput.mouse.Listener | None):
        if listener is not None:
            listener.stop()
        self.ls = None

    def startListener(self):
        self.ls = pynput.mouse.Listener(on_click=self.getValue)
        self.ls.start()

    def processValue(self, x, y, button: Button, pressed, _):
        self.setText(button.name)
        return button
