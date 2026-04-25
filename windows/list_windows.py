import win32gui
import win32process
import win32con
import psutil


SYSTEM_TITLES = [
    "Paramètres",
    "Settings",
    "Windows Input Experience",
    "Expérience d’entrée Windows",
    "Search"
]


def get_process_name(pid):
    try:
        return psutil.Process(pid).name()
    except:
        return ""


def is_real_app(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False

    if win32gui.GetParent(hwnd) != 0:
        return False

    title = win32gui.GetWindowText(hwnd)
    if not title:
        return False

    # filtrer fenêtres système
    for s in SYSTEM_TITLES:
        if s.lower() in title.lower():
            return False

    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    if ex_style & win32con.WS_EX_TOOLWINDOW:
        return False

    return True


def get_taskbar_apps():
    seen = set()
    results = []

    def callback(hwnd, _):
        if not is_real_app(hwnd):
            return

        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process_name = get_process_name(pid)

        key = (title, pid)
        if key in seen:
            return
        seen.add(key)

        results.append({
            "title": title,
            "pid": pid,
            "process": process_name,
            "hwnd": hwnd
        })

    win32gui.EnumWindows(callback, None)
    return results


if __name__ == "__main__":
    apps = get_taskbar_apps()

    for i in apps:
        print(f"{i.get("title")}  {i.get("process")}")