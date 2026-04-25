
import win32api
import ctypes

def list_monitors():
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    monitors = win32api.EnumDisplayMonitors()
    return [win32api.GetMonitorInfo(x[0]) for x in monitors]

if __name__ == "__main__":
    print(list_monitors())