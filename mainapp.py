import sys
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QTabWidget, QVBoxLayout, QLineEdit, QCheckBox, QTextEdit
from PyQt5.QtWidgets import QGroupBox, QListWidget, QPushButton
from PyQt5.QtCore import QSize
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
        self.resize(680, 900)

        main_layout = QVBoxLayout()
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_monitor_tab(), "Monitor")
        tab_widget.addTab(self.create_settings_tab(), "Settings")
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
        tab_widget.setCurrentIndex(0)
        self.worker = None

    def create_monitor_tab(self):
        monitor_tab = QWidget()
        layout = QVBoxLayout()
        monitor_tab.setLayout(layout)

        targets_groupbox = QGroupBox("Targets")
        targets_layout = QVBoxLayout()
        targets_list = QListWidget()
        targets_list.addItems(["BTCUSDT", "DOGEUSDT"])
        targets_layout.addWidget(targets_list)
        targets_groupbox.setLayout(targets_layout)
        layout.addWidget(targets_groupbox)

        holdings_groupbox = QGroupBox("Holdings")
        holdings_layout = QVBoxLayout()
        holdings_list = QListWidget()
        holdings_list.addItems(["BTCUSDT", "DOGEUSDT"])
        holdings_layout.addWidget(holdings_list)
        holdings_groupbox.setLayout(holdings_layout)
        layout.addWidget(holdings_groupbox)

        logs_groupbox = QGroupBox("Logs")
        logs_layout = QVBoxLayout()
        self.logs_textedit = QTextEdit()
        self.logs_textedit.setReadOnly(True)
        self.logs_textedit.append("2024/04/03 09:45:23 just opened 23 AVAX")
        logs_layout.addWidget(self.logs_textedit)
        logs_groupbox.setLayout(logs_layout)
        layout.addWidget(logs_groupbox)


        layout.addSpacing(20)  # Add 20 pixels spacing

        self.start_button = QPushButton("Start")
        # Connect signals
        self.start_button.pressed.connect(self.start_worker)
        self.start_button.released.connect(self.stop_worker)
        self.start_button.clicked.connect(self.toggle_start_button_text)


        layout.addWidget(self.start_button)
        layout.addStretch()  # Add stretch to push the start_button to the bottom


        return monitor_tab

    def create_settings_tab(self):

        settings = QSettings("config.ini", QSettings.IniFormat)
        
        settings_tab = QWidget()
        layout = QVBoxLayout()
        settings_tab.setLayout(layout)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("api_key")
        self.api_key_input.setText(settings.value("last_input1", ""))
        layout.addWidget(self.api_key_input)

        self.api_secret_input = QLineEdit()
        self.api_secret_input.setPlaceholderText("api_secret")
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        self.api_secret_input.setText(settings.value("last_input2", ""))
        
        layout.addSpacing(20)  # Add 20 pixels spacing
        layout.addWidget(self.api_secret_input)

        return settings_tab

    def toggle_start_button_text(self):
        current_text = self.start_button.text()
        if current_text == "Start":
            self.start_button.setText("Stop")
        else:
            self.start_button.setText("Start")

    def start_worker(self):
        if not self.worker or not self.worker.isRunning():
            input1 = self.api_key_input.text()
            input2 = self.api_secret_input.text()
            self.logs_textedit.clear()
            self.worker = Worker(input1, input2)
            self.worker.update_signal.connect(self.update_log)
            self.worker.start()
    
    def stop_worker(self):
        if self.worker:
            self.worker.requestInterruption()
    
    def update_log(self, message):
        self.logs_textedit.append(message)

    def closeEvent(self, event):
        # Save the last input values when the dialog is closed
        settings = QSettings("config.ini", QSettings.IniFormat)
        settings.setValue("last_input1", self.api_key_input.text())
        settings.setValue("last_input2", self.api_secret_input.text())
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec_())
