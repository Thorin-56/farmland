from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt


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
        self.vbox.addWidget(_object)
        self.items.update({name: _object})

    def remove(self, name):
        self.vbox.removeWidget(self.items[name])
        self.items[name].deleteLater()
        self.items.pop(name)

    def clear(self):
        while self.vbox.count():
            widget = self.vbox.takeAt(0)
            if widget.widget():
                widget.widget().deleteLater()


class QScrollCategorie(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.headers = QScroll(self)
        self.headers_height = 30
        self.headers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.headers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.headers.vbox.setContentsMargins(0, 0, 0, 0)
        self.headers.vbox.setDirection(QVBoxLayout.Direction.LeftToRight)
        self.headers.vbox.setSpacing(0)
        self.headers.setGeometry(0, 0, self.width(), self.headers_height)

        self.scroll: QScroll | None = None

        self.categ: dict[str, QWidget] = {}
        self.categ_h = {}
        self.categSlc = None

    def setCurrentCateg(self, name):
        if self.categSlc:
            self.categ_h[self.categSlc].setStyleSheet("color: white")
            self.scroll.hide()

        self.categSlc = name
        self.scroll = self.categ[name]
        self.scroll.setGeometry(0, self.headers_height, self.width(), self.height() - self.headers_height)
        self.scroll.show()

        self.categ_h[name].setStyleSheet("color: red")

    def addCateg(self, name):
        if name in self.categ.keys():
            return

        scroll = QScroll(self)
        scroll.hide()
        self.categ.update({name: scroll})
        button = QPushButton(name)
        button.setFixedSize(100, self.headers_height - 4)
        button.clicked.connect(lambda _, fi=name: self.setCurrentCateg(fi))
        self.categ_h.update({name: button})
        self.headers.add(button, name)
        if self.categSlc is None:
            self.setCurrentCateg(name)

    def removeCateg(self, name):
        if name not in self.categ.keys():
            return
        self.categ[name].deleteLater()
        self.categ_h[name].deleteLater()
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


