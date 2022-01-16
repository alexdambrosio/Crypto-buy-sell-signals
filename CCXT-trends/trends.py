import ccxt
import pandas as pd
pd.set_option('display.max_rows', None)
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
import schedule
import time

exchange = ccxt.binance()

# define function for true range
def tr(df):
    df['previous_close'] = df['close'].shift(1)
    df['high-low'] = df['high'] - df['low']
    df['high-pc'] = abs(df['high'] - df['previous_close'])
    df['low-pc'] = abs(df['low'] - df['previous_close'])
    tr = df[['high-low', 'high-pc', 'low-pc']].max(axis=1)
    
    return tr

# define average true range
def atr(df, period=14):
    df['tr'] = tr(df)
    the_atr = df['tr'].rolling(period).mean()
    
    return the_atr

# define supertrend 
def supertrend(df, period=7, atr_multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
        
    return df

def check_buy_sell_signals(df):
    print('checking for buys and sell')
    print(df.tail())
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1 

    print(last_row_index)
    print(previous_row_index)

    if not df["in_uptrend"][previous_row_index] and df["in_uptrend"][last_row_index]:
        print("changed to uptrend, buy")

    if df["in_uptrend"][previous_row_index] and not df["in_uptrend"][last_row_index]:
        print("changed to downtrend, sell")
    
    

def run_bot():
    print(f'Fetching new bars for {datetime.now().isoformat()}')
    bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1m', limit = 50)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit = 'ms')
    #print(df)
    supertrend_data = supertrend(df)
    check_buy_sell_signals(supertrend_data)

schedule.every(3).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)