import sys
from PyQt5.QtCore import Qt,QEvent,QObject
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QTabWidget, QVBoxLayout, QLineEdit, QCheckBox, QTextEdit
from PyQt5.QtWidgets import QGroupBox, QListWidget, QPushButton, QSizePolicy
from PyQt5.QtCore import QSize
from libs.OrderWork import OrderWorker

class MonitorWorker(QThread):
    msg_signal = pyqtSignal(str) # msg from dialog
    account_info_signal = pyqtSignal(str)
    mm_rate = pyqtSignal(float)
    def __init__(self,
                apikey,
                secretkey,
                ):
        super().__init__()
        self.apikey = apikey
        self.secretkey = secretkey
        self.msg_signal.connect(self.receive_message)

    # receive message dynamically from dialog
    def receive_message(self, message):
        msg_arr = message.split(',')
        self.apikey = msg_arr[0]
        self.secretkey = msg_arr[1]
        print(f'just received {message}')

    # every 5 seconds, check spot holdings and position
    # then refresh the UI
    def fetch_account_informations(self):
        # check current 
        print('time to ask account infomation')
        self.account_info_signal.emit(f"position:")
        pass

    def run(self):
        while(True):
            # Sleep for 10 second
            print("fetch account")
            self.msleep(10000)

# class for api_secret lose focus
class FocusFilter(QObject):
  def __init__(self, widget,callback):
    super().__init__(widget)
    self.widget = widget
    self.callback = callback

  def eventFilter(self, obj, event):
    if obj == self.widget and event.type() == QEvent.FocusOut:
      # "Line Edit lost focus!"
      print("loseFocus")
      if(self.callback):
          self.callback()
      return True  
    else:
      return super().eventFilter(obj, event)


class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.order_worker = None
        self.monitor_worker = None
        self.setWindowTitle("FRate Arbitrageur")
        self.resize(680, 900)

        main_layout = QVBoxLayout()
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_monitor_tab(), "Monitor")
        tab_widget.addTab(self.create_settings_tab(), "Settings")
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
        tab_widget.setCurrentIndex(0)
        

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
        logs_layout.addWidget(self.logs_textedit)
        logs_groupbox.setLayout(logs_layout)
        layout.addWidget(logs_groupbox)
        layout.addSpacing(20)  # Add 20 pixels spacing


        # Start Button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.toggle_start_button_text)

        layout.addWidget(self.start_button)
        layout.addStretch()  # Add stretch to push the start_button to the bottom

        return monitor_tab

    def on_lose_focus(self):
        if len(self.api_key_input.text())>0 and len(self.api_secret_input.text())>0:
            api_key = self.api_key_input.text()
            secret_key = self.api_secret_input.text()
            self.monitor_worker.msg_signal.emit(f'{api_key},{secret_key}')


    def create_settings_tab(self):
        settings = QSettings("config.ini", QSettings.IniFormat)
        settings_tab = QWidget()
        vbox = QVBoxLayout()
        groupBox = QGroupBox("Parameters")
        groupBoxLayout = QVBoxLayout()

        # Create labels and text input fields
        label1 = QLabel("Api Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("api_key")
        apikey = settings.value("last_input1", "")
        self.api_key_input.setText(apikey)
        
        label2 = QLabel("Api Secret:")
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setPlaceholderText("api_secret")
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        secretkey = settings.value("last_input2", "")
        self.api_secret_input.setText(secretkey)
        # Install the event filter and bind lose focus event 
        _filter = FocusFilter(self.api_secret_input,self.on_lose_focus)
        self.api_secret_input.installEventFilter(_filter)

        
        label3 = QLabel("Symbol:")
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("DOGEUSDT")
        self.symbol_input.setText(settings.value("symbol", ""))
        
        label4 = QLabel("MM Rate Limit(%)")
        self.mmrate_input = QLineEdit()
        self.mmrate_input.setPlaceholderText("30")
        self.mmrate_input.setText(settings.value("mmrate", ""))

        # Add labels and text input fields to groupbox layout
        groupBoxLayout.addWidget(label1)
        groupBoxLayout.addWidget(self.api_key_input)
        groupBoxLayout.addWidget(label2)
        groupBoxLayout.addWidget(self.api_secret_input)
        groupBoxLayout.addWidget(label3)
        groupBoxLayout.addWidget(self.symbol_input)
        groupBoxLayout.addWidget(label4)
        groupBoxLayout.addWidget(self.mmrate_input)

        # entry and exit tab
        tab_widget = QTabWidget()
        entry_tab = QWidget()
        exit_tab = QWidget()
        label5 = QLabel("Descrpancy: +%")
        hbox1 = QVBoxLayout()
        hbox1.addWidget(label5)
        entry_tab.setLayout(hbox1)
        label6 = QLabel("Descrpancy: -%")
        tab_widget.addTab(entry_tab, "Entry")
        tab_widget.addTab(exit_tab,"Exit")
        entry_mode = int(settings.value("entrymode", 0))
        tab_widget.setCurrentIndex(entry_mode)
        def on_tab_changed(index):
            # save current entry mode when tab change
            settings = QSettings("config.ini", QSettings.IniFormat)
            settings.setValue("entrymode",index)
            
        tab_widget.tabBarClicked.connect(on_tab_changed)
        groupBoxLayout.addWidget(tab_widget)

        # Set layout of groupbox
        groupBox.setLayout(groupBoxLayout)

        # Add groupbox to the main layout
        vbox.addWidget(groupBox, alignment=Qt.AlignTop)

        # Set geometry of the dialog
        settings_tab.setLayout(vbox)

        # when api_key & secret is valid, start worker
        if len(apikey)>0 and len(secretkey)>0:
            if not self.monitor_worker or not self.monitor_worker.isRunning():
                self.monitor_worker = MonitorWorker(apikey,secretkey)
                self.monitor_worker.start()
                print(self.monitor_worker)
        
        return settings_tab

    def toggle_start_button_text(self):
        current_text = self.start_button.text()
        if current_text == "Start":
            self.start_worker()
            self.start_button.setText("Stop")
        else:
            self.stop_worker()
            self.start_button.setText("Start")

    def start_worker(self):
        apikey = self.api_key_input.text()
        secretkey = self.api_secret_input.text()
        if len(apikey)>0 and len(secretkey)>0:
            if not self.order_worker or not self.order_worker.isRunning():                
                symbol = self.symbol_input.text()
                self.logs_textedit.clear()    
                self.order_worker = OrderWorker(apikey,secretkey,symbol)
                self.order_worker.update_signal.connect(self.update_log)
                self.order_worker.start()

            if not self.monitor_worker or not self.monitor_worker.isRunning():
                self.monitor_worker = MonitorWorker(apikey,secretkey)
                self.monitor_worker.start()
        
    def stop_worker(self):
        if self.order_worker:
            self.order_worker.requestInterruption()
    
    def update_log(self, message):
        self.logs_textedit.append(message)

    def closeEvent(self, event):
        # Save the last input values when the dialog is closed
        settings = QSettings("config.ini", QSettings.IniFormat)
        settings.setValue("last_input1", self.api_key_input.text())
        settings.setValue("last_input2", self.api_secret_input.text())
        settings.setValue("symbol", self.symbol_input.text())
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec_())
