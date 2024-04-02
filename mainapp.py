import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal

class Worker(QThread):
    """
    Worker thread class to execute the background task in a separate thread.
    Emits a signal (`progress_update`) to communicate with the main thread.
    """
    progress_update = pyqtSignal(int)  # Signal to emit progress updates

    def __init__(self, parent=None):
        super().__init__(parent)
        self.count = 0

    def run(self):
        while True:
            self.count += 1
            self.sleep(1)  # Simulate work for demonstration
            self.progress_update.emit(self.count)  # Emit progress update
            if self.count>10:
                self.count=0
                print('emit signal')
               
class MainWindow(QMainWindow):
    """
    Main window class for the PyQt5 application.
    Receives progress updates from the worker thread and updates the UI.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Background Task Example")

        self.label = QLabel("Progress: 0")
        self.button = QPushButton("Stop")

        self.button.clicked.connect(self.stop_worker)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)

        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

        # Create the worker thread and connect its signal to the update_progress slot
        self.worker = Worker()
        self.worker.progress_update.connect(self.update_progress)
        self.worker.start()  # Start the worker thread when the window is created

    def update_progress(self, count):
        """
        Slot to receive progress updates from the worker thread and update the label.
        """
        self.label.setText(f"Progress: {count}")

    def stop_worker(self):
        """
        Slot to stop the worker thread when the button is clicked.
        """
        self.worker.terminate()  # Send a termination signal to the worker thread

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
