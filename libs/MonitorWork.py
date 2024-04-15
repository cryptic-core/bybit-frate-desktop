import time
import json
from datetime import datetime
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
        self.positionlist = {}
        self.account_info = {}
        self.calc_total_income()

    # receive message dynamically from dialog
    def receive_message(self, message):
        msg_arr = message.split(',')
        self.apikey = msg_arr[0]
        self.secretkey = msg_arr[1]
        print(f'just received {message}')

    def fetch_position_info(self):
        # fetch past funding history for 1 year 
        wallet_res = self.session.get_wallet_balance(accountType="UNIFIED")
        coin_list = wallet_res['result']['list'][-1]['coin']
        coin_dict = {item["coin"]: item for item in coin_list}
        
        position_res = self.session.get_positions(category="linear",settleCoin="USDT")
        usd_value_total = sum( float(pos["positionValue"]) for pos in position_res['result']['list'])
        for pos in position_res['result']['list']: 
            symbol = pos['symbol']
            tick_res = self.session.get_tickers(category='linear',symbol=symbol)
            frate_runtime = float(tick_res['result']['list'][-1]['fundingRate'])*100*3*365
            nextFundingTime = datetime.utcfromtimestamp(float(tick_res['result']['list'][-1]['nextFundingTime'])/1000).strftime('%y/%m/%d %H:%M')
            ratio = "{:.2f}%".format(float(pos['positionValue'])/usd_value_total*100)
            if not symbol in self.positionlist:
                self.positionlist[symbol] = {
                    "Symb":symbol,
                    "SPOT":coin_dict[symbol[:-4]]['walletBalance'],
                    "PERP":pos['size'],
                    "USD Value": "{:.2f}".format(float(pos['positionValue'])),
                    "Ratio%": ratio,
                    "Total Income":0,
                    "8H Income":0, 
                    "Next Fund. APY":f'{frate_runtime}%',
                    "Next Fund. Time":nextFundingTime
                }
            else:
                self.positionlist[symbol]['SPOT'] = coin_dict[symbol[:-4]]['walletBalance']
                self.positionlist[symbol]['PERP'] = pos['size']
                self.positionlist[symbol]["USD Value"] = "{:.2f}".format(float(pos['positionValue']))
                self.positionlist[symbol]["Ratio%"] = ratio
                self.positionlist[symbol]["Next Fund. APY"] = f'{frate_runtime}%'
                self.positionlist[symbol]["Next Fund. Time"] = nextFundingTime

    def calc_total_income(self):
        self.fetch_position_info()
        self.fetch_account_info()
        # fetch all history income 2 years
        all_funding_accumulated = 0
        all_interest_accumulated = 0
        all_funding_tx = []
        all_interest_tx = []
        end_time = int(time.time()*1000)
        while True:
            fundinglog_res = self.session.get_transaction_log(
                accountType="UNIFIED",
                category='linear',
                type='SETTLEMENT',
                endTime=end_time
            )
            if len(fundinglog_res['result']['list'])<1:break
            for tx in fundinglog_res['result']['list']:
                all_funding_accumulated += float(tx['funding'])
                all_funding_tx.append(tx)
            end_time = int(fundinglog_res['result']['list'][-1]['transactionTime'])-3000
        
        print(all_funding_accumulated)
        while True:
            interest_hist = self.session.get_transaction_log(
                accountType="UNIFIED",
                category='spot',
                type="INTEREST"
            )
            if len(interest_hist['result']['list'])<1:break
            for tx in fundinglog_res['result']['list']:
                all_interest_accumulated += float(tx['funding'])
                all_interest_tx.append(tx)
            end_time = int(interest_hist['result']['list'][-1]['transactionTime'])-3000
        print(all_interest_tx)
        
    # every 5 seconds, check spot holdings and position
    # then refresh the UI
    def fetch_account_info(self):
        # check current 
        self.fetch_position_info()

        info_interestRate = self.session.spot_margin_trade_get_vip_margin_data(currency="USDT",vipLevel="No VIP")
        houly_borrowRate = float(info_interestRate['result']['vipCoinList'][-1]['list'][0]['hourlyBorrowRate']) * 100
        yearly_borrowRate = houly_borrowRate * 24 * 365
        print("{:.2f}%".format(yearly_borrowRate))
        
        # send update mm_rate & im_rate to dialog
        msg_body = {"houly_borrowRate":houly_borrowRate,"yearly_borrowRate":yearly_borrowRate}
        msg = f'monitorworkmsg#{json.dumps(msg_body)}'
        self.account_info_to_dlg.emit(msg)
        
        # send account info to Order Worker
        self.account_info_signal.emit(f"position:here")
        
    def run(self):
        while(True):
            # Sleep for 10 second
            
            self.fetch_account_info()
            self.msleep(10000)
