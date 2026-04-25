import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QFrame
from PySide6.QtCore import Qt, QSize, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QRegion, QCursor
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(2)

class Window(QMainWindow):
    def __init__(self, x, y, d):
        super().__init__()
        self.x = x
        self.y = y
        self.window_size = d  # Fenêtre plus grande pour voir le contexte
        self.circle_size = self.window_size  # Cercle au centre

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setFixedSize(QSize(self.window_size, self.window_size))

        # Centrer la fenêtre
        screens = QApplication.screens()
        screen = geom = ratio = None
        for screen in screens:
            geom = screen.availableGeometry()
            ratio = screen.devicePixelRatio()

            screen2 = QApplication.screenAt(QPoint(x//ratio, y//ratio))
            if screen == screen2:
                break

        real_width = int(geom.width() * ratio)
        real_height = int(geom.height() * ratio)

        self.move(int(x / ratio) - self.window_size // 2, int(y / ratio) - self.window_size //2)

        # Fenêtre complètement transparente
        self.setAttribute(Qt.WA_TranslucentBackground)

    def move(self, x, y):
        # Centrer la fenêtre
        screens = QApplication.screens()
        for screen in screens:
            geom = screen.availableGeometry()
            ratio = screen.devicePixelRatio()

            screen2 = QApplication.screenAt(QPoint(x // ratio, y // ratio))
            if screen == screen2:
                break

        super().move(int(x / ratio) - self.window_size // 2, int(y / ratio) - self.window_size // 2)

    def paintEvent(self, event):

        """Peindre un cercle semi-transparent sur fond transparent"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Cercle blanc semi-transparent (127 = 50%)
        brush = QBrush(QColor(255, 255, 255, 127))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)

        # Centrer le cercle dans la fenêtre
        x = (self.window_size - self.circle_size) // 2
        y = (self.window_size - self.circle_size) // 2
        painter.drawEllipse(x, y, self.circle_size, self.circle_size)

        # Cercle blanc semi-transparent (127 = 50%)
        brush = QBrush(QColor(0, 0, 0, 255))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)

        # Centrer le cercle dans la fenêtre
        x = (self.window_size - 3) // 2
        y = (self.window_size - 3) // 2
        painter.drawEllipse(x, y, 3, 3)

        painter.end()

    def mousePressEvent(self, event):
        self.hide()


class WindowBorder(QMainWindow):
    def __init__(self, x, y, width, height, x_start, x_end, y_start, y_end):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.x_start = x_start
        self.x_end = x_end
        self.y_start = y_start
        self.y_end = y_end


        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setFixedSize(QSize(self.width, self.height))

        self.move(self.x, self.y)

        # Fenêtre complètement transparente
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        brush = QBrush(QColor(255, 255, 255, 127))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRect(QRect(0, 0, self.width, self.height))

        painter.setCompositionMode(QPainter.CompositionMode_Clear)

        painter.drawRect(QRect(self.x_start, self.y_start, self.width - self.x_start - self.x_end, self.height - self.y_start - self.y_end))

        painter.end()

    def mousePressEvent(self, event):
        self.hide()


def delete_border(window):
    pass
    import ctypes
    from ctypes import byref, sizeof, c_int

    hwnd = window.winId().__int__()

    dwmapi = ctypes.windll.dwmapi

    # Constantes
    DWMWA_BORDER_COLOR = 34
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36
    DWMWA_WINDOW_CORNER_PREFERENCE = 33

    DWMWCP_DONOTROUND = 1

    # Supprimer bordure (mettre transparent)
    border_color = c_int(0x00000000)
    dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR, byref(border_color), sizeof(border_color))

    # Supprimer coins arrondis (Windows 11)
    corner_pref = c_int(DWMWCP_DONOTROUND)
    dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, byref(corner_pref), sizeof(corner_pref))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    _window = WindowBorder(100, 100, 150, 150, 0, 0, 0, 0)

    _window.show()
    # delete_border(_window)
    app.exec()

