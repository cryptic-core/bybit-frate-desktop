import sys
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLineEdit, QCheckBox, QTextEdit, QLabel
from pybit.unified_trading import WebSocket


class Worker(QThread):

    update_signal = pyqtSignal(str)

    def __init__(self, input1, input2):
        super().__init__()
        self.input1 = input1
        self.input2 = input2
        self.ws = WebSocket(
            testnet=False,
            channel_type="linear",
        )
        self.ws.orderbook_stream(50, "BTCUSDT", self.handle_message)

    def handle_message(self,message):
        if self.isInterruptionRequested():return
        # todo : entry log
        self.update_signal.emit(f"{message['data']['b'][0]}")
    
    def run(self):
        while True:
            if self.isInterruptionRequested():
                self.ws.exit()
                break
            # Simulate work
            self.msleep(1000)  # Sleep for 1 second


class MyDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dialog Example")

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

        # Load and set the last input values
        settings = QSettings("config.ini", QSettings.IniFormat)
        self.text_input1.setText(settings.value("last_input1", ""))
        self.text_input2.setText(settings.value("last_input2", ""))

        self.worker = None

    def toggle_worker(self, state):
        if state == 2:  # Checked state
            if not self.worker or not self.worker.isRunning():
                input1 = self.text_input1.text()
                input2 = self.text_input2.text()
                self.log_area.clear()
                self.worker = Worker(input1, input2)
                self.worker.update_signal.connect(self.update_log)
                self.worker.start()
        else:
            if self.worker:
                self.worker.requestInterruption()
                    


    def update_log(self, message):
        self.log_area.append(message)

    def closeEvent(self, event):
        # Save the last input values when the dialog is closed
        settings = QSettings("config.ini", QSettings.IniFormat)
        settings.setValue("last_input1", self.text_input1.text())
        settings.setValue("last_input2", self.text_input2.text())
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec_())
