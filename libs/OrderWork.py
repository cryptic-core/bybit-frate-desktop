import math
import json
import time
from datetime import datetime
from PyQt5.QtCore import Qt,QEvent,QObject
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from pybit.unified_trading import WebSocket
from pybit.unified_trading import HTTP

# Order processor class
class OrderWorker(QThread):
    trigger_from_dlg = pyqtSignal(str) # toggle from dialog
    order_res_to_dlg = pyqtSignal(str)
    aggregate_book_to_dlg = pyqtSignal(str)
    pyqtSignal(str)
    def __init__(self,
                 apikey,
                 secretkey,
                 symbol='DOGEUSDT',
                 descrpancy=0.001,
                 mode=0,
                 targetsz=0,
                 mlotplier=2
                 ):
        super().__init__()
        self.apikey = apikey
        self.secretkey = secretkey
        self.symbol=symbol
        self.descrpancy = descrpancy
        self.mode='entry' if mode==0 else 'exit'
        self.targetsz = targetsz
        self.mlotplier = max(1,mlotplier) 
        self.trigger_from_dlg.connect(self.on_trigger_from_dlg)
        # inner infomation
        self.start_entry = False
        self.swap_order_id = ''
        self.asset_info = {}
        self.position = {}
        self.spotholding = {}
        self.margin_rate = 95

        bTestnet = False
        self.session = HTTP(
            testnet=bTestnet,
            api_key=apikey,
            api_secret=secretkey,
        )
        info_spot = self.session.get_instruments_info(
            category="spot",
            symbol=self.symbol,
        )
        info_swap = self.session.get_instruments_info(
            category="linear",
            symbol=self.symbol,
        )
        min_spot_amt = float(info_spot['result']['list'][0]['lotSizeFilter']['minOrderQty'])
        min_ord_swap = float(info_swap['result']['list'][0]['lotSizeFilter']['minOrderQty'])
        min_sz = max(min_ord_swap,min_spot_amt)
        ord_step = float(info_swap['result']['list'][0]['lotSizeFilter']['qtyStep'])
        multiplier = math.ceil(min_sz/ord_step)
        self.min_ord = multiplier * ord_step * self.mlotplier

        self.priceScale = float(info_swap['result']['list'][0]['priceScale'])
        self.lastordertime = time.time()
        self.init_ws(apikey,secretkey)

    def init_ws(self,apikey,secretkey):
        self.wsspot = WebSocket(
            testnet=False,
            channel_type="spot",
        )
        self.wsperp = WebSocket(
            testnet=False,
            channel_type="linear",
        )
        self.ws_private = WebSocket(
            testnet=False,
            channel_type="private",
            api_key=apikey,
            api_secret=secretkey,
            trace_logging=False,
        )
        self.ws_private.order_stream(self.handle_order_message)

        # 推送都不會變動，原因不明
        self.ws_private.wallet_stream(self.handle_cur_wallet)
        
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

            # toggle filter
            if not self.start_entry:return

            # time filter
            curtime = time.time()
            if (curtime - self.lastordertime)<1.5:return
            self.lastordertime = time.time()
            if len(self.swap_order_id)>0:return

            # qty filter
            curswap_sz = float(self.position[self.symbol]['size']) if self.symbol in self.position else 0
            if curswap_sz>=self.targetsz:return

            # MM filter
            if(self.margin_rate >= 95):return

            # check should entry
            if diffperc > self.descrpancy:    
                # place limit order swap
                px = (float(self.synthbook[instId]['SwAPx']) + float(self.synthbook[instId]['SwBPx']))/2
                res = self.session.place_order(
                    category="linear",
                    symbol=instId,
                    side="Sell" if self.mode=='entry' else 'Buy',
                    orderType="Limit",
                    price=px,
                    qty=str(self.min_ord),
                )
                if res['retCode'] != 0:
                    print(res['retMsg'])
                else:
                    self.swap_order_id = res['result']['orderId']
        else:
            diff = self.synthbook[instId]['SwAPx']-self.synthbook[instId]['bidPx']
            diffperc = diff/self.synthbook[instId]['bidPx']
            aggregate_book['spot'] = self.synthbook[instId]['bidPx']
            aggregate_book['swap'] = self.synthbook[instId]['SwAPx']
            aggregate_book['perc'] = "{:.2f}".format(diffperc * 100)
            # send curr price info back to dlg
            self.aggregate_book_to_dlg.emit( json.dumps(aggregate_book))

            curtime = time.time()
            if (curtime - self.lastordertime)<1000:return
            # check should exit
            if diffperc < self.descrpancy:
                pass
        # ( debug )
        #print(self.synthbook)
         
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
            qty = float(ordinfo['qty'])
            symb = ordinfo['symbol']
            #usdNotion = float(self.synthbook[symb]['askPx'])*qty
            ordres = self.session.place_order(
                category="spot",
                symbol=symb,
                marketUnit='baseCoin',
                side="Buy" if self.mode=='entry' else "Sell",
                orderType="Market",
                qty=str(qty),
            )
            if ordres['retCode'] == 0:
                self.swap_order_id = ''
                dtstr = datetime.today().strftime('%m-%d %H:%M:%S')
                self.order_res_to_dlg.emit(f"{dtstr} just increase {qty} {symb} position.")
            else:
                print(ordres['retMsg'])
        else: # if spot is filled, 
            qty = ordinfo['qty']

    # update position & holdings on callback
    def handle_cur_wallet(self,message):
        if not 'data' in message : return

    # receive message dynamically from dialog
    def on_trigger_from_dlg(self, contex):
        content = json.loads(contex)
        self.start_entry = content["toggle"]
        self.mode == 'entry' if content["mode"]==0 else 'exit'
        self.apikey = content['apikey']
        self.symbol = content['symbol']
        self.secretkey = content['apisecret']
        self.margin_rate = float(content['mmrate'])
        self.mlotplier = float(content['mlotplier'])
        self.targetsz = float(content['targetsz'])

        # restart ws
        self.wsspot.exit()
        self.wsperp.exit()
        self.init_ws(self.apikey,self.secretkey)
    
    # receive account info from monitor worker class
    def on_account_info_msg(self,msg):

        # print(f'on receive {msg} from monitor')
        info_wallet = self.session.get_wallet_balance(accountType="UNIFIED") # account margin
        accountBalance ="{:.2f}".format( float(info_wallet['result']['list'][-1]['totalEquity']) )
        imrate_f = float(info_wallet['result']['list'][-1]['accountIMRate'])*100
        mmrate_f = float(info_wallet['result']['list'][-1]['accountMMRate'])*100
        accountIMRate = "{:.2f}".format( imrate_f )
        accountMMRate = "{:.2f}".format( mmrate_f )
        # update margin rate
        self.margin_rate = imrate_f + mmrate_f
        avilBalance = float(info_wallet['result']['list'][-1]['totalAvailableBalance'])
        USDLoan = 0
        for coin in info_wallet['result']['list'][-1]['coin']:
            if coin['coin']=='USDT':
                USDLoan = float(coin['borrowAmount'])
        current_leverage = (USDLoan/avilBalance)+1

        # historical funding history
        frate_hist = self.session.get_funding_rate_history(
            category="linear",
            symbol=self.symbol
        )
        most_recent_frate_apy ="{:.2f}".format( float(frate_hist['result']['list'][0]['fundingRate'])*3*365*100 )
        
        # send update mm_rate & im_rate to dialog
        msg_body = {"accountBalance":accountBalance,"frate_apy_8H":most_recent_frate_apy,"imrate":accountIMRate,"mmrate":accountMMRate}
        msg = f'orderworkmsg#{json.dumps(msg_body)}'
        self.order_res_to_dlg.emit(msg)


        #self.swap_order_id = ''
        wallet_res = self.session.get_wallet_balance(accountType="UNIFIED")
        for asset in wallet_res['result']['list'][-1]['coin']:
            symbol = f'{asset["coin"]}USDT'
            if symbol!=self.symbol:continue
            self.asset_info[symbol] = asset

        position_res = self.session.get_positions(category="linear", symbol=self.symbol)
        for pos in position_res['result']['list']:
            symbol = pos['symbol']
            if symbol != self.symbol:continue
            self.position[symbol] = pos
        
        curswap_sz = float(self.position[self.symbol]['size']) if self.symbol in self.position else 0
        curspot_sz = float(self.asset_info[self.symbol]['equity']) if self.symbol in self.asset_info else 0
        diff = curswap_sz - curspot_sz
        d_qty = abs(diff)
        # try to fill up the diff
        if d_qty >= self.min_ord:
            d_side = 'Buy' if diff>0 else 'Sell'
            multiplier = math.floor(d_qty/self.min_ord)
            numord = multiplier*self.min_ord
            ordres = self.session.place_order(
                    category="spot",
                    symbol=self.symbol,
                    marketUnit='baseCoin',
                    side=d_side,
                    orderType="Market",
                    qty=str(numord),
                )
            if ordres['retCode'] == 0:
                dtstr = datetime.today().strftime('%m-%d %H:%M:%S')
                self.order_res_to_dlg.emit(f"{dtstr} try to fill up the difference {diff} amount")
                # check diff is done, continue to place new order
                print(f'try to fill up the difference')
            else:
                print(ordres['retMsg'])
            

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