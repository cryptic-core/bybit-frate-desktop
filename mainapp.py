import sys
import json
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QTabWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit
from PyQt5.QtWidgets import QGroupBox, QListWidget, QPushButton
from libs.OrderWork import OrderWorker
from libs.MonitorWork import MonitorWorker
from libs.utils import FocusFilter
from ui.Widgets import TableWidget

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.order_worker = None
        self.monitor_worker = None
        settings = QSettings("config.ini", QSettings.IniFormat)
        self.target_symbol = settings.value("symbol","")
        self.setWindowTitle("FRate Arbitrageur")
        self.resize(780, 900)
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

        info_group_box = QGroupBox("Price Info")
        info_layout = QVBoxLayout() 
        self.lbb_spot_px = QLabel(f"{self.target_symbol} Spot:")
        self.lbb_spot_px.setAlignment(Qt.AlignLeft)
        self.lbb_swap_px = QLabel(f"{self.target_symbol} Perp:")
        self.lbb_swap_px.setAlignment(Qt.AlignLeft)  
        self.lbb_desc_pc = QLabel(f"Difference")
        self.lbb_desc_pc.setAlignment(Qt.AlignLeft)  

        # Create horizontal layout for each info line
        info_line_layout = QHBoxLayout()
        info_line_layout.addWidget(self.lbb_spot_px)
        info_line_layout.addWidget(self.lbb_swap_px)
        info_line_layout.addWidget(self.lbb_desc_pc)
        #info_line_layout.setStretch(0, 0) # Stretch label1 to fill remaining space
        info_layout.addLayout(info_line_layout)
        info_group_box.setLayout(info_layout)
        layout.addWidget(info_group_box)


        accinfo_grp_box = QGroupBox("Account Info")
        accinfo_layout = QHBoxLayout()
        self.lbb_acc_balance = QLabel("Account Balance: 45142")
        self.lbb_acc_balance.setAlignment(Qt.AlignLeft)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True) 
        #self.lbb_acc_balance.setFont(font)
        accinfo_layout.addWidget(self.lbb_acc_balance)
        self.lbb_im_rate = QLabel("IM Rate: 45%")
        self.lbb_im_rate.setAlignment(Qt.AlignLeft)
        accinfo_layout.addWidget(self.lbb_im_rate)
        self.lbb_mm_rate = QLabel("MM Rate: 15%")
        self.lbb_mm_rate.setAlignment(Qt.AlignLeft)
        accinfo_layout.addWidget(self.lbb_mm_rate)
        accinfo_grp_box.setLayout(accinfo_layout)
        layout.addWidget(accinfo_grp_box)

        yieldinfo_grp_box = QGroupBox("Yield Info")
        yieldinfo_layout = QHBoxLayout()
        self.lbb_real_income_8h = QLabel("Real Income 8H:       $18.135 usd")
        self.lbb_real_income_8h.setAlignment(Qt.AlignLeft)
        yieldinfo_layout.addWidget(self.lbb_real_income_8h)
        self.lbb_apy_8h = QLabel("APY 8H:       56%")
        self.lbb_apy_8h.setAlignment(Qt.AlignLeft)
        yieldinfo_layout.addWidget(self.lbb_apy_8h)
        yieldinfo_grp_box.setLayout(yieldinfo_layout)
        layout.addWidget(yieldinfo_grp_box)


        lendinfo_grp_box = QGroupBox("Lending Info")
        lendinfo_layout = QHBoxLayout()
        self.lbb_lendrate_8h = QLabel("Lending rate 8hr:   10%")
        self.lbb_lendrate_8h.setAlignment(Qt.AlignLeft)
        lendinfo_layout.addWidget(self.lbb_lendrate_8h)
        lendinfo_grp_box.setLayout(lendinfo_layout)
        layout.addWidget(lendinfo_grp_box)


        holdings_groupbox = QGroupBox("Positions")
        holdings_layout = QVBoxLayout()
        self.table_widget = TableWidget()
        holdings_layout.addWidget(self.table_widget)
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
        curmode = 'Entry'
        settings = QSettings("config.ini", QSettings.IniFormat)
        mode_id = int(settings.value("entrymode",0))
        if(mode_id==1):
            curmode = 'Exit'
        self.start_button = QPushButton(f"Start {curmode}")
        self.start_button.clicked.connect(self.toggle_start_button_text)

        layout.addWidget(self.start_button)
        layout.addStretch()  # Add stretch to push the start_button to the bottom

        return monitor_tab

    # when user input secretkey completed
    def on_secret_lose_focus(self):
        if len(self.api_key_input.text())>0 and len(self.api_secret_input.text())>0:
            api_key = self.api_key_input.text()
            secret_key = self.api_secret_input.text()
            self.monitor_worker.secretkey_signal.emit(f'{api_key},{secret_key}')
    
    def on_symbol_lose_focus(self):
        self.target_symbol = self.symbol_input.text()

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
        _filter = FocusFilter(self.api_secret_input,self.on_secret_lose_focus)
        self.api_secret_input.installEventFilter(_filter)

        
        label3 = QLabel("Symbol:")
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("DOGEUSDT")
        self.symbol_input.setText(settings.value("symbol", ""))
        _filter = FocusFilter(self.symbol_input,self.on_symbol_lose_focus)
        self.symbol_input.installEventFilter(_filter)
        
        label4 = QLabel("Do not over this MM Rate Limit(%)")
        self.mmrate_input = QLineEdit()
        self.mmrate_input.setPlaceholderText("30")
        self.mmrate_input.setText(settings.value("mmrate", ""))

        label_a1 = QLabel("Num Lot Multiplier")
        self.mlot_input = QLineEdit()
        self.mlot_input.setPlaceholderText("30")
        self.mlot_input.setText(settings.value("mlot", "2"))

        # Add labels and text input fields to groupbox layout
        groupBoxLayout.addWidget(label1)
        groupBoxLayout.addWidget(self.api_key_input)
        groupBoxLayout.addWidget(label2)
        groupBoxLayout.addWidget(self.api_secret_input)
        groupBoxLayout.addWidget(label3)
        groupBoxLayout.addWidget(self.symbol_input)
        groupBoxLayout.addWidget(label_a1)
        groupBoxLayout.addWidget(self.mlot_input)
        groupBoxLayout.addWidget(label4)
        groupBoxLayout.addWidget(self.mmrate_input)

        # entry and exit tab
        tab_widget = QTabWidget()
        entry_tab = QWidget()
        exit_tab = QWidget()
        label5 = QLabel("Descrpancy: +%")
        self.entry_dif = QLineEdit()
        self.entry_dif.setPlaceholderText("0.1")
        self.entry_dif.setText(settings.value("entrydif", ""))

        label6 = QLabel("Target Size")
        self.tgt_amt_entry = QLineEdit()
        self.tgt_amt_entry.setPlaceholderText("10000")
        self.tgt_amt_entry.setText(settings.value("tgtentrysz", ""))

        hbox1 = QVBoxLayout()
        hbox1.addWidget(label5)
        hbox1.addWidget(self.entry_dif)
        hbox1.addWidget(label6)
        hbox1.addWidget(self.tgt_amt_entry)
        entry_tab.setLayout(hbox1)

        label7 = QLabel("Descrpancy: -%")
        self.exit_dif = QLineEdit()
        self.exit_dif.setPlaceholderText("0.1")
        self.exit_dif.setText(settings.value("exitdif", ""))
        label8 = QLabel("Target Size")
        self.tgt_amt_exit = QLineEdit()
        self.tgt_amt_exit.setPlaceholderText("0")
        self.tgt_amt_exit.setText(settings.value("tgtexitsz", ""))

        hbox2 = QVBoxLayout()
        hbox2.addWidget(label7)
        hbox2.addWidget(self.exit_dif)
        hbox2.addWidget(label8)
        hbox2.addWidget(self.tgt_amt_exit)
        exit_tab.setLayout(hbox2)

        tab_widget.addTab(entry_tab, "Entry")
        tab_widget.addTab(exit_tab,"Exit")
        entry_mode = int(settings.value("entrymode", 0))
        tab_widget.setCurrentIndex(entry_mode)
        def on_tab_changed(index):
            # save current entry mode when tab change
            settings = QSettings("config.ini", QSettings.IniFormat)
            settings.setValue("entrymode",index)
            curmode = "Entry" if index==0 else "Exit"
            self.start_button.setText(f"Start {curmode}")
            
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
                self.monitor_worker.account_info_to_dlg.connect(self.update_log)
                self.monitor_worker.start()
                print(self.monitor_worker)
        
        return settings_tab

    def toggle_start_button_text(self):
        current_text = self.start_button.text()
        settings = QSettings("config.ini", QSettings.IniFormat)
        mode = int(settings.value("entrymode",0))
        curmode = "Entry" if mode==0 else "Exit"
        if current_text == f"Start {curmode}":
            self.start_worker()
            self.start_button.setText("Stop")
        else:
            self.stop_worker()
            self.start_button.setText(f"Start {curmode}")
            

    def start_worker(self):
        apikey = self.api_key_input.text()
        secretkey = self.api_secret_input.text()
        if len(apikey)>0 and len(secretkey)>0:
            if not self.order_worker or not self.order_worker.isRunning():                
                symbol = self.symbol_input.text()
                settings = QSettings("config.ini", QSettings.IniFormat)
                mode = int(settings.value("entrymode",0))
                descrpancy = float(self.entry_dif.text()) if mode==0 else float(self.exit_dif.text())
                descrpancy *= 0.01
                tgtsz = float(self.tgt_amt_entry.text()) if mode==0 else float(self.tgt_amt_exit.text())
                mlotplier = float(self.mlot_input.text())
                self.logs_textedit.clear()
                self.order_worker = OrderWorker(apikey,secretkey,symbol,descrpancy,mode,tgtsz,mlotplier)
                self.order_worker.order_res_to_dlg.connect(self.update_order_log)
                self.order_worker.aggregate_book_to_dlg.connect(self.on_aggregate_book)
                self.order_worker.start()

            if not self.monitor_worker or not self.monitor_worker.isRunning():
                self.monitor_worker = MonitorWorker(apikey,secretkey)
                self.monitor_worker.account_info_to_dlg.connect(self.update_log)
                # connect order worker if it is active
                if self.order_worker:
                    self.monitor_worker.account_info_signal.connect(self.order_worker.on_account_info_msg)
                # start monitor
                self.monitor_worker.start()
            else:
                # monitor is already started, just connect them
                self.monitor_worker.account_info_to_dlg.connect(self.update_log)
                # connect order worker if it is active
                if self.order_worker:
                    self.monitor_worker.account_info_signal.connect(self.order_worker.on_account_info_msg)
    
    def stop_worker(self):
        if self.order_worker:
            self.order_worker.requestInterruption()
    
    def on_aggregate_book(self,agbooks):
        agbooks_dict = json.loads(agbooks)
        spot_px = agbooks_dict['spot']
        swap_px = agbooks_dict['swap']
        difperc = agbooks_dict['perc']
        self.lbb_spot_px.setText(f'{self.target_symbol} Spot: {str(spot_px)}')
        self.lbb_swap_px.setText(f'{self.target_symbol} Perp: {str(swap_px)}')
        self.lbb_desc_pc.setText(f'Difference: {str(difperc)}%')
        # debug
        # print(f'spot px:{spot_px} swap_px:{swap_px} difperc:{difperc}')
        

    def update_log(self, message):
        if '#' in message: # is imrate message
            borrwo_rate_obj = json.loads( message.split('#')[1] )
            self.lbb_lendrate_8h.setText(f"Lending rate 8hr:   {borrwo_rate_obj['yearly_borrowRate']}")
            self.lbb_real_income_8h.setText(f"Real Income 8H:       ${borrwo_rate_obj['recent8HIncome']} usd")    
        elif '$' in message: # is position info message
            position_info_list = list( json.loads(message.split('$')[1]) )
            pass
        else:
            self.logs_textedit.append(message)
    
    def update_order_log(self, message):
        if '#' in message: # is json message
            msg_json = json.loads( message.split('#')[1] )
            most_recent_frate_apy = msg_json['frate_apy_8H']
            imrate = msg_json['imrate']
            mmrate = msg_json['mmrate']
            accountBalance = msg_json['accountBalance']
            self.lbb_acc_balance.setText(f"Account Balance: {accountBalance}")
            self.lbb_im_rate.setText(f"IM Rate: {imrate}%")
            self.lbb_mm_rate.setText(f"MM Rate: {mmrate}%")
            self.lbb_apy_8h.setText(f"APY 8H:       {most_recent_frate_apy}%")
        else:
            self.logs_textedit.append(message)

    def closeEvent(self, event):
        # Save the last input values when the dialog is closed
        settings = QSettings("config.ini", QSettings.IniFormat)
        settings.setValue("last_input1", self.api_key_input.text())
        settings.setValue("last_input2", self.api_secret_input.text())
        settings.setValue("symbol", self.symbol_input.text())
        settings.setValue("mmrate", self.mmrate_input.text())
        settings.setValue("entrydif", self.entry_dif.text())
        settings.setValue("exitdif", self.exit_dif.text())
        settings.setValue("tgtentrysz", self.tgt_amt_entry.text())
        settings.setValue("tgtexitsz", self.tgt_amt_exit.text())
        settings.setValue("mlot", self.mlot_input.text())
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec_())
