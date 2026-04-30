import asyncio
import sys

from qasync import QApplication, QEventLoop

from gui import MainWindows

if __name__ == '__main__':
    sys.argv += ['-platform', 'windows:darkmode=2']
    app = QApplication(sys.argv)

    main_loop = QEventLoop(app)
    asyncio.set_event_loop(main_loop)

    windows = MainWindows()
    windows.show()

    with main_loop:
        main_loop.run_forever()
