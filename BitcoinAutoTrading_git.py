import time
import pyupbit
import datetime
import requests

access = "your access"  # API
secret = "your secret"  # API
myToken = "your token"  # slack token

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
                             headers={"Authorization": "Bearer " + token},
                             data={"channel": channel, "text": text}
                             )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

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

def get_buying_ratio(ticker, risk):
    """구매 비중 구하기"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    range_ratio = (df.iloc[0]['high'] - df.iloc[0]['low'])/df.iloc[0]['close']
    buying_ratio = risk/range_ratio
    ratio = min([1, round(buying_ratio, 2)])
    return ratio

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")    # 날짜가 바뀌면 매일 아침 시작 알림 띄우기하자
post_message(myToken,"#coin", "Autotrade start")

# 값초기화
buy_result, daily_msg, sell_result = None, None, None

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")  # 9:00
        end_time = start_time + datetime.timedelta(days=1)  # 9:00 + 1일
        ratio = get_buying_ratio("KRW-BTC", 0.02)

        if start_time < now < end_time - datetime.timedelta(seconds=60):
            target_price = get_target_price("KRW-BTC", 0.5)
            ma5 = get_ma5("KRW-BTC")
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
            buy_result = None       # buy에서 에러 발생시 다음날 되면 buy_result를 초기화 해줘야함. sell 구분 뒤에 있음 에러 났을 경우 안팔리므로 실행 안됨
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
