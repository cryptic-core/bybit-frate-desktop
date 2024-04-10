import sys
from PyQt5.QtCore import Qt,QEvent,QObject
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from pybit.unified_trading import WebSocket

# Order processor class
class OrderWorker(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self,
                 apikey,
                 secretkey,
                 symbol='DOGEUSDT',
                 descrpancy=0.001,
                 ):
        super().__init__()
        self.apikey = apikey
        self.secretkey = secretkey
        self.symbol=symbol
        self.descrpancy = descrpancy

        # time interval to request current holdings
        self.rest_api_counter = 0

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
        self.wsspot.orderbook_stream(1, self.symbol, self.handle_spot_message)
        self.wsperp.orderbook_stream(1, self.symbol, self.handle_perp_message)
        
    def handle_perp_message(self,message):
        if self.isInterruptionRequested():return

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
    
    def handle_order_message(self,message):
        # if perp order just filled 
        # check num filled and market order spot
        pass
    
    def aggregate_book(self):
        for instId in self.synthbook:
            diff = self.synthbook[instId]['SwBPx']-self.synthbook[instId]['askPx']
            diffperc = diff/self.synthbook[instId]['SwBPx']
            if diffperc > self.descrpancy:
                self.update_signal.emit(f"{instId} has entry chance")
                # place limit order swap
        # ( debug )
        #print(self.synthbook)
                
    # receive account info from monitor worker class
    def on_account_info_msg(self,msg):
        print(f'on receive {msg} from monitor')

    def run(self):
        while True:
            if self.isInterruptionRequested():
                self.wsspot.exit()
                self.wsperp.exit()
                break

            # worker initialization log
            if len(self.synthbook)<1:
                self.update_signal.emit(f"initialized")
            
            # Sleep for 1 second
            self.msleep(1000)