import sys
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLineEdit, QCheckBox, QTextEdit, QLabel


class Worker(QThread):
    update_signal = pyqtSignal(str)

    def run(self):
        while True:
            if self.isInterruptionRequested():
                break

            self.update_signal.emit("Working...")

            # Simulate work
            self.msleep(1000)  # Sleep for 1 second


class MyDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FRate Arbitor")

        layout = QVBoxLayout()

        # First text input
        self.text_input1 = QLineEdit()
        layout.addWidget(self.text_input1)

        # Second text input (Password)
        self.text_input2 = QLineEdit()
        self.text_input2.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.text_input2)

        # Toggle Button
        self.toggle_button = QCheckBox("Start")
        self.toggle_button.stateChanged.connect(self.toggle_worker)
        layout.addWidget(self.toggle_button)

        # Log text area
        layout.addWidget(QLabel("Log:"))
        self.log_area = QTextEdit()
        layout.addWidget(self.log_area)

        self.setLayout(layout)

        self.worker = Worker()
        self.worker.update_signal.connect(self.update_log)

    def toggle_worker(self, state):
        if state == 2:  # Checked state
            if not self.worker.isRunning():
                self.log_area.clear()
                self.worker.start()
        else:
            self.worker.requestInterruption()

    def update_log(self, message):
        self.log_area.append(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec_())
