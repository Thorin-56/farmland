from pynput.mouse import Button
from pynput.keyboard import Key

from DataManager.DataManager import DataManager

TABLE_MOUSE = {
    "left": Button.left,
    "right": Button.right,
    "middle": Button.middle,
}

TABLE_KEY = {
    "left": Key.left,
    "right": Key.right,
    "up": Key.up,
    "down": Key.down,
    "space": Key.space
}
database_manager = DataManager()