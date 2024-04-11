import sys
import json
from PyQt5.QtCore import Qt,QEvent,QObject
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP

# Order processor class
class OrderWorker(QThread):
    order_res_to_dlg = pyqtSignal(str)
    aggregate_book_to_dlg = pyqtSignal(str)
    pyqtSignal(str)
    def __init__(self,
                 apikey,
                 secretkey,
                 symbol='DOGEUSDT',
                 descrpancy=0.001,
                 mode=0,
                 targetsz=0
                 ):
        super().__init__()
        self.apikey = apikey
        self.secretkey = secretkey
        self.symbol=symbol
        self.descrpancy = descrpancy
        self.mode='entry' if mode==0 else 'exit'
        self.targetsz = targetsz
        bTestnet = False
        self.session = HTTP(
            testnet=bTestnet,
            api_key=apikey,
            api_secret=secretkey,
        )
        self.wsspot = WebSocket(
            testnet=bTestnet,
            channel_type="spot",
        )
        self.wsperp = WebSocket(
            testnet=bTestnet,
            channel_type="linear",
        )
        self.ws_private = WebSocket(
            testnet=bTestnet,
            channel_type="private",
            api_key=apikey,
            api_secret=secretkey,
            trace_logging=False,
        )
        self.ws_private.order_stream(self.handle_order_message)
        
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
            self.synthbook[instId]['SwBPx']=float(message['data']['b'][0][0])
            self.synthbook[instId]['SwBSz']=float(message['data']['b'][0][1])
            self.synthbook[instId]['SwAPx']=float(message['data']['a'][0][0])
            self.synthbook[instId]['SwASz']=float(message['data']['a'][0][1])
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
    
    # symbol order size
    # https://api.bybit.com/v5/market/instruments-info?category=spot&symbol=DOGEUSDT&status=Trading
    def handle_order_message(self,message):
        if self.isInterruptionRequested():return
        if not 'data' in message:return
        ordinfo = message['data'][-1]
        isFilled = ordinfo['orderStatus']=='Filled'
        if not isFilled:return
        tgt_side = "Sell" if self.mode=='entry' else "Buy"
        isSideMatch = tgt_side == ordinfo['side']
        if not isSideMatch:return
        isLinear = ordinfo['category']=='linear'
        if isLinear:
            qty = ordinfo['qty']
            symb = ordinfo['symbol']
            ordres = self.session.place_order(
                category="spot",
                symbol=symb,
                side="Buy" if self.mode=='entry' else "Sell",
                orderType="Market",
                qty=qty,
            )
            print(ordres)
            if 'orderId' in ordres:
                self.order_res_to_dlg.emit(f"just create {qty} {symb} position")
        else: # if spot is filled, 
            qty = ordinfo['qty']

    def aggregate_book(self):
        instId = list(self.synthbook.keys())[0] # this tool only care one symbol at a time
        # update aggregate book info back to dialog
        aggregate_book = {"spot":0,"swap":0,"perc":''}
        if self.mode == 'entry':
            diff = self.synthbook[instId]['SwBPx']-self.synthbook[instId]['askPx']
            diffperc = diff/self.synthbook[instId]['SwBPx']  
            aggregate_book['spot'] = self.synthbook[instId]['askPx']
            aggregate_book['swap'] = self.synthbook[instId]['SwBPx']
            aggregate_book['perc'] = "{:.2f}".format(diffperc * 100)
            # send curr price info back to dlg
            self.aggregate_book_to_dlg.emit( json.dumps(aggregate_book))
            # check should entry
            if diffperc > self.descrpancy:
                pass
                # place limit order swap
        else:
            diff = self.synthbook[instId]['SwAPx']-self.synthbook[instId]['bidPx']
            diffperc = diff/self.synthbook[instId]['bidPx']
            aggregate_book['spot'] = self.synthbook[instId]['bidPx']
            aggregate_book['swap'] = self.synthbook[instId]['SwAPx']
            aggregate_book['perc'] = "{:.2f}".format(diffperc * 100)
            # send curr price info back to dlg
            self.aggregate_book_to_dlg.emit( json.dumps(aggregate_book))
            # check should exit
            if diffperc < self.descrpancy:
                pass
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
                self.order_res_to_dlg.emit(f"initialized")
            
            # Sleep for 1 second
            self.msleep(1000)