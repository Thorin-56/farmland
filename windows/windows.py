import ctypes
from ctypes import wintypes

import win32gui


def get_windows_pos(name):
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

    def get_true_window_rect(hwnd):
        # Utilise l'API DWM pour ignorer les bordures invisibles (ombres)
        rect = wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect)
        )
        return rect.left, rect.top, rect.right, rect.bottom

    # Test avec une fenêtre
    hwnd = win32gui.FindWindow(None, name)

    if hwnd:
        # Vérifier si la fenêtre est réduite (iconified)
        if win32gui.IsIconic(hwnd):
            # print("La fenêtre est réduite, les coordonnées ne sont pas valides.")
            return None
        else:
            real_rect = get_true_window_rect(hwnd)
            return real_rect
    else:
        # print("Fenêtre non trouvée.")
        return None
