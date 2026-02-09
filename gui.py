from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from qasync import QEventLoop, asyncSlot
import asyncio
from main import *


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle("AutoFarmland Farmer")
        self.setFixedWidth(500)
        self.setFixedHeight(500)

        self.scrollarea = QScrollArea(self)
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.scrollarea.setWidget(self.widget)
        self.widget.setLayout(self.layout)

        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setGeometry(10, 40, 240, 150)

        for i in point["recolt"]:
            a = QPushButton(f"Recolt {point["dic"][i]}")
            a.clicked.connect(lambda _, fi=i: self.click_s1(fi))
            self.layout.addWidget(a)

        self.edit_frame = QFrame(self)
        self.edit_frame.setGeometry(250, 40, 240, 150)
        self.edit_frame.setStyleSheet("border: 1px solid grey")
        self.edit_frame.hide()

        self.input_edit = QLineEdit(self.edit_frame)
        self.input_edit.setGeometry(5, 5, 100, 30)

        self.save_edit = QPushButton("Save", self.edit_frame)
        self.save_edit.setGeometry(5, 40, 100, 30)
        self.save_edit.setStyleSheet("border-radius: 5px; background: #4444ff")
        self.save_edit.clicked.connect(self.edit_recolt_name)

        self.edit_btn = QPushButton("Edit", self)
        self.edit_btn.clicked.connect(self.sw_edit)
        self.edit_btn.setStyleSheet("background-color: #4444ff; color: white;")
        self.edit_btn.setGeometry(10, 5, 100, 30)

        self.stop_button = QPushButton("Arrêter", self)
        self.stop_button.setGeometry(170, 5, 150, 30)
        self.stop_button.clicked.connect(self.stop_tasks)
        self.stop_button.setStyleSheet("background-color: #ff4444; color: white;")

        self.loop_btn = QPushButton("Lancer", self)
        self.loop_btn.setGeometry(170, 250, 150, 30)
        self.loop_btn.clicked.connect(self.launch_loop)
        self.loop_btn.setStyleSheet("background-color: rgb(100, 250, 100); color: white;")

        self.status_label = QLabel("Prêt", self)
        self.status_label.setGeometry(350, 10, 300, 20)

        # Liste pour suivre les tâches en cours
        self.current_tasks = []
        self.stop_flag = False

        self.pause_event = asyncio.Event()
        self.pause = False

        self.edit = False
        self.slc_recolt = None

    def sw_edit(self):
        self.edit = not self.edit
        if self.edit:
            self.edit_frame.show()
        else:
            self.edit_frame.hide()

    @asyncSlot()
    async def click_s1(self, name):
        if not self.edit:
            await self.start_recolt(name)
        else:
            self.input_edit.setText(point["dic"][name])
            self.slc_recolt = name

    @asyncSlot()
    async def edit_recolt_name(self):
        point["dic"][self.slc_recolt] = self.input_edit.text()
        with open("point.json", "w") as file:
            json.dump(point, file, indent=1)

    @asyncSlot()
    async def start_recolt(self, name):
        self.stop_button.setEnabled(True)
        self.stop_flag = False
        self.status_label.setText(f"Récolte {name} en cours...")

        try:
            task = asyncio.create_task(self.run_recolt_with_stop(name))
            self.current_tasks.append(task)
            await task
            if not self.stop_flag:
                self.status_label.setText(f"Récolte {name} terminée !")
            else:
                self.status_label.setText("Arrêté par l'utilisateur")

        except asyncio.CancelledError:
            self.status_label.setText("Arrêté")
        except Exception as e:
            self.status_label.setText(f"Erreur: {e}")
        finally:
            self.stop_button.setEnabled(False)
            if task in self.current_tasks:
                self.current_tasks.remove(task)

    async def run_recolt_with_stop(self, name):
        await recolt(name)

    def stop_tasks(self):
        self.stop_flag = True
        for task in self.current_tasks:
            task.cancel()
        self.status_label.setText("Arrêt en cours...")

    @asyncSlot()
    async def launch_loop(self):
        tasks = point.get("loop")
        self.loop_btn.setText("en cours")
        while not self.stop_flag:
            for task in tasks:
                match task[0]:
                    case "recolt":
                        await self.start_recolt(task[1])
                    case "sleep":
                        await asyncio.sleep(task[1])
                    case "world":
                        await tp_world(task[1])
                    case "click":
                        print("click")
                if self.stop_flag:
                    break
            if self.stop_flag:
                break
        self.stop_flag = False


if __name__ == '__main__':
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()