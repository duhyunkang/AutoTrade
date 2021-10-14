import time
import pyupbit
import datetime
import requests

access = "key"
secret = "key"
myToken = "key"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
                             headers={"Authorization": "Bearer " + token},
                             data={"channel": channel, "text": text}
                             )

def get_new_ohlcv(hour='9h'):
    df = pyupbit.get_ohlcv(ticker="KRW-BTC", interval='minute60', count=150)
    df_resampling = df.resample('24H', offset=hour).agg(\
                                    {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
    df_new = df_resampling[-6:-1]
    return df_new

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
post_message(myToken,"#coin", "Autotrade start")

# 값초기화
buy_result, daily_msg, sell_result = None, None, None

# 자동매매 시작
while True:
    try:
        df = get_new_ohlcv('11h')       # 이거는 한번만 쓰자
        now = datetime.datetime.now()
        start_time = df.index[-1]  # 11:00
        end_time = start_time + datetime.timedelta(days=1)  # 11:00 + 1일

        # 구매 비중 구하기
        range_ratio = (df.iloc[-1]['high'] - df.iloc[-1]['low']) / df.iloc[-1]['close']
        buying_ratio = 0.02 / range_ratio    # risk 비중은 0.02 (2%)
        ratio = min([1, round(buying_ratio, 2)])

        if start_time < now < end_time - datetime.timedelta(seconds=60):
            target_price = df.iloc[-1]['close'] + (df.iloc[-1]['high'] - df.iloc[-1]['low']) * 0.4  # k=0.4
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            current_price = get_current_price("KRW-BTC")
            daily_msg, sell_result = None, None     # 각 초기화해주고
            if target_price < current_price and ma5 < current_price:
                budget = get_balance("KRW") * ratio         # 잔고에 구매 비중을 곱한 금액만큼만 살것임 (구매 예산)
                # 구매 예산이 5천 이상이고, buy_result가 None 또는 error 일때만
                if budget > 5000 and (buy_result is None or 'error' in buy_result):
                    buy_result = upbit.buy_market_order("KRW-BTC", budget*0.9995)
                    post_message(myToken, "#coin", "BTC buy : " +str(buy_result))

        else:
            btc = get_balance("BTC")
            buy_result = None   # 초기화
            # BTC가 5천원 이상이고, sell_result가 None 또는 error 일때만
            if btc > 0.00008 and (sell_result is None or 'error' in sell_result):
                sell_result = upbit.sell_market_order("KRW-BTC", btc)
                post_message(myToken, "#coin", "BTC sell : " + str(sell_result))
            # 프로그램 가동중임을 알리는 알람
            if daily_msg is None:
                post_message(myToken, "#coin", "program is running")
                daily_msg = "On"
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#coin", e)
        time.sleep(1)
