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


def watchlist_strategy(stock_data):
    buy_date = ''
    position = 0  # 持仓状态 (0: 空仓, 1: 持仓)
    buy_price = 0
    holdings = 0
    buy_date_idx = 0
    atr_sell_price = 0.0
    cooldown_days = 0
    last_sell_idx = 0

    trade_logs = []
    stock_code = stock_data["股票代码"].iloc[0]
    trade_count = 0
    profit_count = 0
    macd_signal_days = 0

    for i in range(1, len(stock_data)):
        formatted_date = stock_data.index[i].date().strftime('%Y-%m-%d')

        if formatted_date == '2024-02-02':
            print("debug")

        open = stock_data["开盘"].iloc[i]
        close = stock_data["收盘"].iloc[i]
        prev_close = stock_data["收盘"].iloc[i - 1]
        high = stock_data["最高"].iloc[i]
        highest_250 = stock_data["highest_250"].iloc[i]
        low = stock_data["最低"].iloc[i]
        volume = stock_data["成交量"].iloc[i]
        days_increase = stock_data["涨跌幅"].iloc[i]
        BBANDS_lower = stock_data["BBANDS_lower"].iloc[i]
        BBANDS_upper = stock_data["BBANDS_upper"].iloc[i]
        BBANDS_middle = stock_data["BBANDS_middle"].iloc[i]
        ma5 = stock_data["ma5"].iloc[i]
        ma10 = stock_data["ma10"].iloc[i]
        ma20 = stock_data["ma20"].iloc[i]
        ma60 = stock_data["ma60"].iloc[i]
        ma250 = stock_data["ma250"].iloc[i]
        macd = stock_data['macd'].iloc[i]
        dif = stock_data['macd_dif'].iloc[i]
        dea = stock_data['macd_dea'].iloc[i]
        dmi_plus = stock_data['dmi_plus'].iloc[i]
        dmi_minus = stock_data['dmi_minus'].iloc[i]
        atr = stock_data['atr'].iloc[i]
        volume_ma5 = stock_data["volume_ma5"].iloc[i]
        rsi = stock_data['rsi'].iloc[i]

        ma250_oversell_strategy = (ma250 - close) / ma250 > 0.3
        bbands_oversell_strategy = close < BBANDS_lower
        rsi_oversell_strategy = rsi < 25

        over_sold_strategy = bool(rsi_oversell_strategy and bbands_oversell_strategy and ma250_oversell_strategy)

        add_watchlist = over_sold_strategy

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
        watchlist_stock = watchlist_strategy(data)

        return watchlist_stock
    except Exception as e:
        print(f"\n{stock_code} 处理失败: {e}")

        return stock_watching(stock_code, '1900-01-01', 0, 0)


if __name__ == "__main__":

    today_str = datetime.today().strftime('%Y-%m-%d 00:00:00')
    output_file = "watchlist_results.csv"
    file_exists = os.path.exists(output_file)

    watching_map = {}

    stock_profits = stock_indicators.get_stock_code()
    '''
    stock_key = '002717'
    stock_profits = {
        stock_key: 0,
        # '002261': 0
    }
    '''
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
