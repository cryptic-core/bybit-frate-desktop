from PyQt5.QtCore import Qt,QEvent,QObject
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from pybit.unified_trading import HTTP

# Account information class
class MonitorWorker(QThread):
    secretkey_signal = pyqtSignal(str) # msg from dialog
    account_info_to_dlg = pyqtSignal(str) # account info msg to dialog
    account_info_signal = pyqtSignal(str) # msg to order worker

    mm_rate = pyqtSignal(float)
    def __init__(self,
                apikey,
                secretkey,
                ):
        super().__init__()
        self.apikey = apikey
        self.secretkey = secretkey
        self.secretkey_signal.connect(self.receive_message)
        self.session = HTTP(
            testnet=False,
            api_key=apikey,
            api_secret=secretkey,
        )


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
        #print('time to ask account infomation')

        info_swap = self.session.get_instruments_info(
            category="linear",
            symbol='DOGEUSDT',
        )
        funding_interval = info_swap['result']['list'][0]['fundingInterval']

        # send account info to Order Worker
        self.account_info_signal.emit(f"position:here")
        # send account info to UI
        # self.account_info_to_dlg.emit(f"position:here")
        pass

    def run(self):
        while(True):
            # Sleep for 10 second
            self.fetch_account_informations()
            self.msleep(10000)
