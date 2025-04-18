from datetime import datetime

import akshare as ak
import numpy as np
import pandas as pd
import talib
import matplotlib.pyplot as plt
import concurrent.futures


def get_stock_code():
    df = pd.read_csv("stock_codes.csv")  # 替换为你的实际文件名

    # 创建map：key为code，value为0
    code_map = {str(code): 0 for code in df['code']}

    # 输出结果
    return code_map


def get_stock_data(stock_code, start_date, end_date):
    stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date,
                                    adjust="qfq")

    stock_data.columns = ['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅',
                          '涨跌额', '换手率']

    # 将日期转换为索引
    stock_data['日期'] = pd.to_datetime(stock_data['日期'])
    stock_data.set_index('日期', inplace=True)

    return stock_data


def calculate_indicators(stock_data):
    close = stock_data['收盘'].values
    high = stock_data['最高'].values
    low = stock_data['最低'].values
    open = stock_data['开盘'].values
    volume = stock_data['成交量'].values.astype(float)

    highest_250 = talib.MAX(high, timeperiod=250)
    stock_data["highest_250"] = highest_250

    # 布林带指标
    stock_data["BBANDS_upper"], stock_data["BBANDS_middle"], stock_data["BBANDS_lower"] = talib.BBANDS(close,
                                                                                                       timeperiod=20,
                                                                                                       nbdevup=2,
                                                                                                       nbdevdn=2)

    # 均线指标
    stock_data["ma10"] = talib.SMA(close, timeperiod=10)
    stock_data["ma5"] = talib.SMA(close, timeperiod=5)
    stock_data["ma20"] = talib.SMA(close, timeperiod=20)
    stock_data["ma60"] = talib.SMA(close, timeperiod=60)
    stock_data["ma250"] = talib.SMA(close, timeperiod=250)

    # 平均交易量
    stock_data["volume_ma5"] = talib.SMA(volume, timeperiod=5)

    # MACD指标
    stock_data["macd_dif"], stock_data["macd_dea"], MACD = talib.MACD(close, fastperiod=12, slowperiod=26,
                                                                      signalperiod=9)
    stock_data["macd"] = (stock_data["macd_dif"] - stock_data["macd_dea"]) * 2

    # DMI指标
    stock_data["dmi_plus"] = talib.PLUS_DI(high, low, close, timeperiod=14)
    stock_data["dmi_minus"] = talib.MINUS_DI(high, low, close, timeperiod=14)

    # atr指标
    stock_data["atr"] = talib.ATR(high, low, close, timeperiod=14)


# 获取板块行情数据
def get_board_concept_name_df():
    stock_board_concept_name_df = ak.stock_board_concept_name_em()

    # 查看数据结构
    print(stock_board_concept_name_df.head())

    # 提取板块名称和涨跌幅
    board_df = stock_board_concept_name_df[['板块名称', '最新价', '涨跌幅']]

    # 按涨跌幅排序
    board_df['涨跌幅'] = board_df['涨跌幅'].astype(str).str.replace('%', '').astype(float)
    board_df = board_df.sort_values(by='涨跌幅', ascending=False)

    # 输出涨幅排名前 10 的板块
    print("涨幅前10的板块：")
    print(board_df.head(10))

    # 输出跌幅排名前 10 的板块
    print("\n跌幅前10的板块：")
    print(board_df.tail(10))


def get_holdings_cost(capital, price):
    shares_per_lot = 100
    max_shares = int(capital // price)

    lots = max_shares // shares_per_lot
    holdings = lots * shares_per_lot

    return holdings


def sell_price_strategy(high, low, atr):
    height = high - low

    if height <= atr:
        sell_price = low - atr
    elif atr < height < 2 * atr:
        sell_price = low - 1.5 * atr
    else:
        sell_price = low - 2 * atr

    return sell_price


# 是否涨停
def cal_limit_up(prev_price, current_price):
    return round(prev_price * 1.10, 2) == current_price


# 放量大跌
def heavy_volume_sell_off(volume, avg_volume, open_price, current_close):
    volume_signal1 = volume > avg_volume * 1.3 and current_close < open_price * 0.97
    volume_signal2 = volume > avg_volume * 1.5 and current_close < open_price * 0.98
    volume_signal3 = volume > avg_volume * 1.8 and current_close < open_price * 0.99

    return volume_signal1 or volume_signal2 or volume_signal3


# 上影线过长
def long_upper_shadow(open, close, high, low, highest_250):
    body = abs(close - open)
    upper_shadow = high - max(close, open)

    if high == highest_250:
        return upper_shadow > body
    else:
        return upper_shadow > body * 2


def trade_strategy(stock_data, capital):
    buy_date = ''
    position = 0  # 持仓状态 (0: 空仓, 1: 持仓)
    buy_price = 0
    # capital = 100000  # 初始资金
    holdings = 0
    buy_date_idx = 0
    atr_sell_price = 0.0
    cooldown_days = 0
    last_sell_idx = 0

    trade_log = []
    stock_code = stock_data["股票代码"].iloc[0]
    trade_count = 0
    profit_count = 0

    for i in range(1, len(stock_data)):
        date = stock_data.index[i].date()
        '''
        if date.strftime('%Y-%m-%d') == '2023-04-06':
            print("debug")
        '''
        open = stock_data["开盘"].iloc[i]
        close = stock_data["收盘"].iloc[i]
        prev_close = stock_data["收盘"].iloc[i - 1]
        highest = stock_data["最高"].iloc[i]
        highest_250 = stock_data["highest_250"].iloc[i]
        lowest = stock_data["最低"].iloc[i]
        volume = stock_data["成交量"].iloc[i]
        days_increase = stock_data["涨跌幅"].iloc[i]
        BBANDS_lower = stock_data["BBANDS_lower"].iloc[i]
        BBANDS_upper = stock_data["BBANDS_upper"].iloc[i]
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

        macd_strategy = 0 < macd and dif > dea and dif > -2 and dea > -2
        dmi_strategy = dmi_plus > dmi_minus
        bbands_strategy = True
        ma510_strategy = ma5 > ma10
        ma20_strategy = ((ma20 > stock_data["ma20"].iloc[i - 1])
                         and (ma20 > stock_data["ma20"].iloc[i - 2])
                         and (stock_data["ma20"].iloc[i - 1] > stock_data["ma20"].iloc[i - 2]))
        ma60_strategy = close > ma60
        volume_ma5_strategy = heavy_volume_sell_off(volume, volume_ma5, open, close)
        volume_ma5_strategy = False
        losing_streak = (close < prev_close) and (prev_close < stock_data["收盘"].iloc[i - 2])
        losing_streak = False
        long_upper_shadow_strategy = long_upper_shadow(open, close, highest, lowest, highest_250)
        long_upper_shadow_strategy = False

        if volume_ma5_strategy or long_upper_shadow_strategy:
            cooldown_days = cooldown_days + 2

        '''
        # 检查是否在冷却期内
        if last_sell_idx != 0:
            days_since_sell = i - last_sell_idx
            if days_since_sell <= cooldown_days:
                # 在冷却期内，不允许买入或卖出
                continue
        '''

        if cooldown_days > 0 and position == 0:
            cooldown_days = cooldown_days - 1
            continue

        buy_strategy = (position == 0 and macd_strategy and dmi_strategy and bbands_strategy and ma510_strategy
                        and ma20_strategy and ma60_strategy)

        if (buy_strategy and volume_ma5_strategy) or losing_streak or long_upper_shadow_strategy:
            buy_strategy = False

        # 买入条件
        if buy_strategy:
            buy_price = close
            position = 1
            holdings = get_holdings_cost(capital, buy_price)
            capital -= holdings * buy_price
            buy_date = stock_data.index[i]
            buy_date_idx = i
            trade_log.append(f"BUY: {stock_data.index[i]} at {buy_price}")
            atr_sell_price = sell_price_strategy(highest, lowest, atr)

        # 卖出条件
        elif position == 1:
            days_held = i - buy_date_idx
            profit_ratio = (close - buy_price) / buy_price
            profit_strategy = profit_ratio > 0.10 or profit_ratio < -0.04
            days_held_strategy = days_held > 5
            atr_strategy = close < atr_sell_price
            days_increase_strategy = (days_increase <= -5) or (days_increase >= 7.5)
            is_limit_up = cal_limit_up(prev_close, close)
            # days_increase_strategy = False

            # sell_strategy = ((macd_strategy is np.False_) or (dmi_strategy is np.False_) or (bbands_strategy is False)
            #                or (ma_strategy is np.False_) or profit_strategy or days_held_strategy or atr_strategy)
            sell_strategy = (profit_strategy or days_held_strategy or atr_strategy or days_increase_strategy
                             or volume_ma5_strategy or long_upper_shadow_strategy or losing_streak)

            if is_limit_up:
                sell_strategy = False

            if sell_strategy:
                sell_price = atr_sell_price if atr_strategy else close
                position = 0
                capital += holdings * sell_price
                holdings = 0
                last_sell_idx = i
                cooldown_days = 5
                trade_log.append(
                    f"SELL: {stock_data.index[i].date()} at {sell_price:.2f} | Profit: {profit_ratio * 100:.2f}% | "
                    f"Days Held: {days_held} | Balance: {capital:.2f}"
                )

                trade_count = trade_count + 1

                if profit_ratio > 0:
                    profit_count = profit_count + 1

    # 最终资金 + 持有股票市值
    if position == 1:
        capital += holdings * stock_data["收盘"].iloc[-1]

    if capital < 0:
        capital = 0

    '''
    # 打印交易记录
    for trade in trade_log:
        print(trade)
    '''

    result_str = (f"\nStockCode: {stock_code}, Final Capital: {capital:.2f} CNY, "
                  f"Winning Rate: {(profit_count / trade_count) * 100:.2f}%,"
                  f"持仓：{position}, 最后一次购买日期为：{buy_date}")
    print(result_str)

    return capital, buy_date, result_str


def cal_profit_to_loss_ratio(stocks_profits):
    # 初始资金
    initial_funds = 100000

    # 计算所有股票的盈亏总和
    total_profit_loss = sum(stocks_profits.values())

    # 计算整体盈亏比
    profit_ratio = total_profit_loss / initial_funds

    # 输出整体盈亏比
    print(f"总盈亏：{total_profit_loss}, 整体盈亏比: {profit_ratio * 100:.2f}%")


def process_stock(stock_code):
    try:
        data = get_stock_data(stock_code, '20240101', '20250418')

        calculate_indicators(data)
        capital, last_buy_date, result_str = trade_strategy(data, base_capital)

        profit = capital - base_capital

        return stock_code, profit, capital, last_buy_date, result_str
    except Exception as e:
        print(f"{stock_code} 处理失败: {e}")
        return stock_code, 0, 0


if __name__ == "__main__":

    stock_profits = get_stock_code()
    buy_map = {}

    '''
    stock_profits = {
        '601398': 0,
        '000796': 0,
        '002475': 0,
    }
    '''
    base_capital = 10000
    capital = base_capital

    today_str = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_stock, code): code for code in stock_profits.keys()}

        for future in concurrent.futures.as_completed(futures):
            stock_code, profit, capital, last_buy_date, result_str = future.result()

            stock_profits[stock_code] = profit
            if last_buy_date == today_str:
                buy_map[stock_code] = result_str

            if capital == 0:
                print(f"{stock_code} 模拟交易失败，终止所有线程")
                break  # 可选：终止后续处理（注意：线程池无法中断已在运行的线程）

    print(buy_map)
    '''
    for stock_code in stock_profits.keys():
        data = get_stock_data(stock_code, '20240101', '20250418')

        calculate_indicators(data)
        capital = trade_strategy(data, base_capital)

        stock_profits[stock_code] = capital - base_capital

        if capital == 0:
            break
    '''
    # cal_profit_to_loss_ratio(stock_profits)

    '''
    # 业绩报表
    # data = ak.stock_yjbb_em(date="20240930")

    # print(data.head())

    # 筹码分布
    # data = ak.stock_cyq_em('000796', adjust="qfq")
    # print(data)

    # get_board_concept_name_df()
    sell_price = sell_price_strategy(10.38, 9.94, 0.42)
    print(sell_price)
    '''
