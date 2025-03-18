import akshare as ak
import numpy as np
import pandas as pd
import talib
import matplotlib.pyplot as plt


def get_stock_data(stock_code, start_date, end_date):
    stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date,
                                    adjust="qfq")
    print(stock_data.columns.tolist())
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

    # 布林带指标
    stock_data["BBANDS_upper"], stock_data["BBANDS_middle"], stock_data["BBANDS_lower"] = talib.BBANDS(close,
                                                                                                       timeperiod=20,
                                                                                                       nbdevup=2,
                                                                                                       nbdevdn=2,
                                                                                                       matype=0)

    # 均线指标
    stock_data["ma10"] = talib.SMA(close, timeperiod=10)
    stock_data["ma5"] = talib.SMA(close, timeperiod=5)

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


def sell_price_strategy(high, low, atr):
    height = high - low

    if height <= atr:
        sell_price = low - atr
    elif atr < height < 2 * atr:
        sell_price = low - 1.5 * atr
    else:
        sell_price = low - 2 * atr

    return sell_price


def trade_strategy(stock_data):
    buy_date = ''
    position = 0  # 持仓状态 (0: 空仓, 1: 持仓)
    buy_price = 0
    capital = 100000  # 初始资金
    holdings = 0
    buy_date_idx = 0
    atr_sell_price = 0.0
    cooldown_days = 5
    last_sell_idx = 0

    trade_log = []

    for i in range(1, len(stock_data)):
        close = stock_data["收盘"].iloc[i]
        highest = stock_data["最高"].iloc[i]
        lowest = stock_data["最低"].iloc[i]
        lower = stock_data["BBANDS_lower"].iloc[i]
        upper = stock_data["BBANDS_upper"].iloc[i]
        ma5 = stock_data["ma5"].iloc[i]
        ma10 = stock_data["ma10"].iloc[i]
        macd = stock_data['macd'].iloc[i]
        dif = stock_data['macd_dif'].iloc[i]
        dea = stock_data['macd_dea'].iloc[i]
        dmi_plus = stock_data['dmi_plus'].iloc[i]
        dmi_minus = stock_data['dmi_minus'].iloc[i]
        atr = stock_data['atr'].iloc[i]

        macd_strategy = macd > 0 and dif > dea
        dmi_strategy = dmi_plus > dmi_minus
        bbands_strategy = True
        ma_strategy = ma5 > ma10

        # 检查是否在冷却期内
        if last_sell_idx != 0:
            days_since_sell = i - last_sell_idx
            if days_since_sell <= cooldown_days:
                # 在冷却期内，不允许买入或卖出
                continue

        # 买入条件
        if position == 0 and macd_strategy and dmi_strategy and bbands_strategy and ma_strategy:
            buy_price = close
            position = 1
            holdings = capital // buy_price
            capital -= holdings * buy_price
            buy_date = stock_data.index[i]
            buy_date_idx = i
            trade_log.append(f"BUY: {stock_data.index[i]} at {buy_price}")
            atr_sell_price = sell_price_strategy(highest, lowest, atr)

        # 卖出条件
        elif position == 1:
            date = stock_data.index[i].date()
            days_held = i - buy_date_idx
            profit_ratio = (close - buy_price) / buy_price
            profit_strategy = profit_ratio > 0.10
            days_held_strategy = days_held > 10
            atr_strategy = close < atr_sell_price

            sell_strategy = ((macd_strategy is np.False_) or (dmi_strategy is np.False_) or (bbands_strategy is False)
                             or (ma_strategy is np.False_) or profit_strategy or days_held_strategy or atr_strategy)

            if sell_strategy:
                sell_price = atr_sell_price if atr_strategy else close
                position = 0
                capital += holdings * sell_price
                holdings = 0
                last_sell_idx = i
                trade_log.append(
                    f"SELL: {stock_data.index[i].date()} at {sell_price:.2f} | Profit: {profit_ratio * 100:.2f}% | "
                    f"Days Held: {days_held}"
                )

    # 最终资金 + 持有股票市值
    if position == 1:
        capital += holdings * stock_data["收盘"].iloc[-1]

    # 打印交易记录
    for trade in trade_log:
        print(trade)

    print(f"\n💰 Final Capital: {capital:.2f} CNY")


def manual_dmi(df, timeperiod=14):
    # 计算 True Range (TR)
    df['high_low'] = df['最高'] - df['最低']
    df['high_close'] = (df['最高'] - df['收盘'].shift(1)).abs()
    df['low_close'] = (df['最低'] - df['收盘'].shift(1)).abs()

    df['TR'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)

    # 计算 +DM 和 -DM
    df['+DM'] = np.where(df['最高'].diff() > df['最低'].diff(),
                         df['最高'].diff().clip(lower=0), 0)
    df['-DM'] = np.where(df['最低'].diff() > df['最高'].diff(),
                         df['最低'].diff().clip(lower=0), 0)

    # 平滑 TR, +DM, -DM（Wilder's smoothing）
    smooth_factor = timeperiod
    df['ATR'] = df['TR'].rolling(window=smooth_factor).mean()
    df['+DI'] = 100 * (df['+DM'].rolling(window=smooth_factor).mean() / df['ATR'])
    df['-DI'] = 100 * (df['-DM'].rolling(window=smooth_factor).mean() / df['ATR'])

    # 计算 ADX
    df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])
    df['ADX'] = df['DX'].rolling(window=smooth_factor).mean()

    print(df[['收盘', '+DI', '-DI', 'ADX']])


data = get_stock_data('002879', '20220301', '202203018')

calculate_indicators(data)
trade_strategy(data)

# get_board_concept_name_df()
