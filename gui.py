import sys
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

        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setGeometry(10, 40, 480, 200)

        for i in point["recolt"]:
            a = QPushButton(f"Recolt {i}")
            a.clicked.connect(lambda _, fi=i: self.start_recolt(fi))
            self.layout.addWidget(a)

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
        """Exécute la récolte avec vérification du stop"""
        await recolt(name)

    def stop_tasks(self):
        self.stop_flag = True
        for task in self.current_tasks:
            task.cancel()
        self.status_label.setText("Arrêt en cours...")

    @asyncSlot()
    async def launch_loop(self):
        tasks = ["farm", "tree", "animals", "sell"]
        self.loop_btn.setText("en cours")
        while not self.stop_flag:
            for task in tasks:
                await self.start_recolt(task)
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