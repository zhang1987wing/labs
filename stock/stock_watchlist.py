import os
from datetime import datetime

import concurrent.futures
import csv

import stock_indicators
from stock_watching import stock_watching


# 预期买入股价
def expected_buy_price(open, close, high, low, highest_250):
    """
    1、ma5从下往上穿过ma10，且ma5 > ma10
    2、macd金叉发生在macd附近
    3、布林带收盘价大于中线
    4、RSI未超过80
    5、收盘价大于各个均线
    5、均线显示
    """
    if high == highest_250:
        return round(high * 1.05, 2)

# 超卖策略
def func_oversell_strategy(stock_data):
    position = 0  # 持仓状态 (0: 空仓, 1: 持仓)
    trade_logs = []

    for i in range(1, len(stock_data)):
        # debug
        formatted_date = stock_data.index[i].date().strftime('%Y-%m-%d')

        if formatted_date == '2024-02-02':
            print("debug")

        stock_code = stock_data["股票代码"].iloc[0]
        close = stock_data["收盘"].iloc[i]
        ma250 = stock_data["ma250"].iloc[i]
        BBANDS_lower = stock_data["BBANDS_lower"].iloc[i]
        rsi = stock_data['rsi'].iloc[i]

        # 超卖策略
        ma250_oversell_strategy = (ma250 - close) / ma250 > 0.3
        bbands_oversell_strategy = close < BBANDS_lower
        rsi_oversell_strategy = rsi < 25

        strategy = bool(rsi_oversell_strategy and bbands_oversell_strategy and ma250_oversell_strategy)

        add_watchlist = strategy

        if add_watchlist:
            if position == 0:
                buy_price = close
                position = 1
                buy_date = stock_data.index[i]
                trade_logs.append(stock_watching(stock_code, buy_date.date(), 1, buy_price))
            else:
                position = 1
                trade_log = trade_logs[len(trade_logs) - 1]
                trade_log.watching_days = trade_log.watching_days + 1
        else:
            position = 0
            continue

    return trade_logs


# ma5金叉策略
def func_ma5_golden_cross_strategy(stock_data):
    position = 0  # 持仓状态 (0: 空仓, 1: 持仓)
    trade_logs = []

    for i in range(1, len(stock_data)):
        # debug
        formatted_date = stock_data.index[i].date().strftime('%Y-%m-%d')

        if formatted_date == '2024-02-02':
            print("debug")

        stock_code = stock_data["股票代码"].iloc[0]

        close = stock_data["收盘"].iloc[i]
        ma5 = round(stock_data["ma5"].iloc[i], 2)
        ma10 = round(stock_data["ma10"].iloc[i], 2)
        ma60 = round(stock_data["ma60"].iloc[i], 2)

        # ma5均线金叉策略
        ma510_strategy = bool(ma5 > ma10 and stock_data["ma5"].iloc[i - 1] <= stock_data["ma10"].iloc[i - 1])
        ma60_strategy = close > ma60

        add_watchlist = ma510_strategy and ma60_strategy

        if add_watchlist:
            if position == 0:
                buy_price = close
                position = 1
                buy_date = stock_data.index[i]
                trade_logs.append(stock_watching(stock_code, buy_date.date(), 1, buy_price))
            else:
                position = 1
                trade_log = trade_logs[len(trade_logs) - 1]
                trade_log.watching_days = trade_log.watching_days + 1
        else:
            position = 0
            continue

    return trade_logs


def get_watchlist(stock_data):

    stock_code = stock_data["股票代码"].iloc[0]

    # trade_logs = func_oversell_strategy(stock_data)
    trade_logs = func_ma5_golden_cross_strategy(stock_data)

    # 打印交易记录
    for trade_log in trade_logs:
        print(trade_log)

    if len(trade_logs) == 0:
        return stock_watching(stock_code, '1900-01-01', 0, 0)
    else:
        return trade_logs[len(trade_logs) - 1]


def process_stock(stock_code):
    try:
        data = stock_indicators.get_stock_data(stock_code, '20230101', '20250516')

        stock_indicators.calculate_indicators(data)
        watchlist_stock = get_watchlist(data)

        return watchlist_stock
    except Exception as e:
        print(f"\n{stock_code} 处理失败: {e}")

        return stock_watching(stock_code, '1900-01-01', 0, 0)


if __name__ == "__main__":

    today_str = datetime.today().strftime('%Y-%m-%d 00:00:00')
    output_file = "watchlist_results.csv"
    file_exists = os.path.exists(output_file)

    watching_map = {}
    '''
    stock_profits = stock_indicators.get_stock_code()
    '''
    stock_key = '002688'
    stock_profits = {
        stock_key: 0,
        # '002261': 0
    }

    strategy_type = 2

    with open(output_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(['stock_code', 'result'])  # 写入表头

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(process_stock, code): code for code in stock_profits.keys()}

            for future in concurrent.futures.as_completed(futures):
                watching_stock = future.result()

                if str(watching_stock.watching_date) == today_str:
                    watching_map[watching_stock.stock_code] = watching_stock

                writer.writerow([watching_stock.stock_code, watching_stock])  # 写入一行记录

    print(f'\n处于观察的股票总量为：{len(watching_map)}')
    print(watching_map)