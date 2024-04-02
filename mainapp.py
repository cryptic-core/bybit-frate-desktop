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
        self.wsspot = WebSocket(
            testnet=False,
            channel_type="spot",
        )
        self.wsperp = WebSocket(
            testnet=False,
            channel_type="linear",
        )
        self.synthbook = {}
        # https://api.bybit.com/derivatives/v3/public/instruments-info
        self.wsspot.orderbook_stream(1, "DOGEUSDT", self.handle_spot_message)
        self.wsperp.orderbook_stream(1, "DOGEUSDT", self.handle_perp_message)
        

    def handle_perp_message(self,message):
        if self.isInterruptionRequested():return
        # todo : entry log
        instId = message['data']['s']
        if not instId in self.synthbook:
            self.synthbook[instId] = {
                'bidPx':float(message['data']['b'][0][0]),
                'bidSz':float(message['data']['b'][0][1]),
                'askPx':float(message['data']['a'][0][0]),
                'askSz':float(message['data']['a'][0][1]),

                'SwBPx':float(message['data']['b'][0][0]),
                'SwBSz':float(message['data']['b'][0][1]),
                'SwAPx':float(message['data']['a'][0][0]),
                'SwASz':float(message['data']['a'][0][1]),
            }
        else:
            self.synthbook[instId]['bidPx']=float(message['data']['b'][0][0])
            self.synthbook[instId]['bidSz']=float(message['data']['b'][0][1])
            self.synthbook[instId]['askPx']=float(message['data']['a'][0][0])
            self.synthbook[instId]['askSz']=float(message['data']['a'][0][1])
        self.aggregate_book()
    
    def handle_spot_message(self,message):
        if self.isInterruptionRequested():return
        # todo : entry log
        instId = message['data']['s']
        if not instId in self.synthbook:
            self.synthbook[instId] = {
                'bidPx':float(message['data']['b'][0][0]),
                'bidSz':float(message['data']['b'][0][1]),
                'askPx':float(message['data']['a'][0][0]),
                'askSz':float(message['data']['a'][0][1]),

                'SwBPx':float(message['data']['b'][0][0]),
                'SwBSz':float(message['data']['b'][0][1]),
                'SwAPx':float(message['data']['a'][0][0]),
                'SwASz':float(message['data']['a'][0][1]),
            }
        else:
            self.synthbook[instId]['bidPx']=float(message['data']['b'][0][0])
            self.synthbook[instId]['bidSz']=float(message['data']['b'][0][1])
            self.synthbook[instId]['askPx']=float(message['data']['a'][0][0])
            self.synthbook[instId]['askSz']=float(message['data']['a'][0][1])
        self.aggregate_book()
    
    def aggregate_book(self):
        
        for instId in self.synthbook:
            diff = self.synthbook[instId]['SwBPx']-self.synthbook[instId]['askPx']
            diffperc = diff/self.synthbook[instId]['SwBPx']
            #if diffperc > 0.0005:
            if diffperc > 0:
                self.update_signal.emit(f"{instId} has entry chance")
        pass

    def run(self):
        while True:
            if self.isInterruptionRequested():
                self.wsspot.exit()
                self.wsperp.exit()
                break
            # Simulate work
            self.msleep(1000)  # Sleep for 1 second


class MyDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FRate Arbitrageur")

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
