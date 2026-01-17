import pyautogui
from ctypes import windll
import win32gui
import json
import asyncio

stop_event = asyncio.Event()

pyautogui.FAILSAFE = True
hdc = windll.user32.GetDC(0)

hwnd = win32gui.FindWindow(None, "Farmland")

stop = False

point: dict
with open("point.json") as file:
  point = json.load(file)

async def press(key, time):
    pyautogui.keyDown(key)
    await asyncio.sleep(time)
    pyautogui.keyUp(key)

def coo(x, y):
    rect = win32gui.GetWindowRect(hwnd)
    pos = rect[0], rect[1] + 90
    taille = rect[2] - pos[0], rect[3] - pos[1]
    return x*taille[0]+pos[0], y*taille[1]+pos[1]

# def getColor(x, y, save_img=False):
#     color: int = windll.gdi32.GetPixel(hdc, x, y)
#     r, g, b = color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF
#     if save_img:
#         a = Image.new("P", (10, 11), (r, g, b))
#         a.save("img.png")
#     return color

async def click_map():
    pyautogui.click(coo(*point["gui"]["map"]))

async def swip_map():
    pyautogui.dragTo(coo(0.9, 0.5))
    pyautogui.dragRel(-300, 0, 0.2)
    await asyncio.sleep(0.3)

async def click_recolt():
    pyautogui.click(coo(0.5, 0.85))
    await asyncio.sleep(3)

async def tp_spawn(name):
    await click_map()
    await swip_map()
    pyautogui.click(coo(*point["tp"][name]))

async def recolt(name):
    await tp_spawn(point["recolt"][name]["tp"])
    await asyncio.sleep(0.3)
    for x, y in point["recolt"][name]["move"]:
        await press(x, y)
    await click_recolt()

if __name__ == '__main__':

    async def main():
        while True:
            win32gui.SetForegroundWindow(hwnd)
            await recolt("farm")
            await recolt("animals")
            await recolt("tree")
            await recolt("sell")
            await asyncio.sleep(60*2)

    asyncio.run(main())