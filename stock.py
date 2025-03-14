import akshare as ak
import numpy as np
import pandas as pd
import talib
import matplotlib.pyplot as plt


def get_stock_data(stock_code, start_date, end_date):
    stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date,
                                    adjust="qfq")
    print(stock_data.columns.tolist())
    stock_data.columns = ["date", "open", "close", "high", "low", "volume", "turnover", "amplitude", "change_pct",
                          "change_amount"]

    # 将日期转换为索引
    stock_data["date"] = pd.to_datetime(stock_data["date"])
    stock_data.set_index("date", inplace=True)

    return stock_data


def calculate_indicators(stock_data):
    close = stock_data['close'].values
    high = stock_data['high'].values
    low = stock_data['low'].values
    open = stock_data['open'].values

    # 布林带指标
    stock_data["BBANDS_upper"], stock_data["BBANDS_middle"], stock_data["BBANDS_lower"] = talib.BBANDS(close,
                                                                                                       timeperiod=20,
                                                                                                       nbdevup=2,
                                                                                                       nbdevdn=2,
                                                                                                       matype=0)

    # 均线指标
    stock_data["ma10"] = talib.SMA(stock_data["close"], timeperiod=10)
    stock_data["ma5"] = talib.SMA(stock_data["close"], timeperiod=5)

    # MACD指标
    stock_data["macd_dif"], stock_data["macd_dea"], MACD = talib.MACD(stock_data["close"], fastperiod=12, slowperiod=26,
                                                                      signalperiod=9)
    stock_data["macd"] = (stock_data["macd_dif"] - stock_data["macd_dea"]) * 2

    # DMI指标
    stock_data["dmi_plus"] = talib.PLUS_DI(high, low, close, timeperiod=14)
    stock_data["dmi_minus"] = talib.MINUS_DI(high, low, close, timeperiod=14)


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


def trade_strategy(stock_data):
    buy_date = ''
    position = 0  # 持仓状态 (0: 空仓, 1: 持仓)
    buy_price = 0
    capital = 100000  # 初始资金
    holdings = 0

    trade_log = []

    for i in range(1, len(stock_data)):
        close = stock_data["close"].iloc[i]
        lower = stock_data["BBANDS_lower"].iloc[i]
        upper = stock_data["BBANDS_upper"].iloc[i]
        ma5 = stock_data["ma5"].iloc[i]
        ma10 = stock_data["ma10"].iloc[i]
        macd = stock_data['macd'].iloc[i]
        dif = stock_data['dif'].iloc[i]
        dea = stock_data['dea'].iloc[i]
        dmi_plus = stock_data['dmi_plus'].iloc[i]
        dmi_minus = stock_data['dmi_minus'].iloc[i]

        macd_strategy = macd > 0 and dif > dea
        dmi_strategy = dmi_plus > dmi_minus
        bbands_strategy = close < lower
        ma_strategy = ma5 > ma10

        # 买入条件
        if position == 0 and macd_strategy and dmi_strategy and bbands_strategy and ma_strategy:
            buy_price = close
            position = 1
            holdings = capital // buy_price
            capital -= holdings * buy_price
            buy_date = stock_data.index[i]
            trade_log.append(f"BUY: {stock_data.index[i]} at {buy_price}")

        # 卖出条件
        elif position == 1:
            days_held = (stock_data.index[i] - buy_date).days
            profit_ratio = (close - buy_price) / buy_price

            if macd_strategy == False or dmi_strategy == False or bbands_strategy == False or ma_strategy == False:
                sell_price = close
                position = 0
                capital += holdings * sell_price
                holdings = 0
                trade_log.append(
                    f"SELL: {stock_data.index[i].date()} at {sell_price:.2f} | Profit: {profit_ratio * 100:.2f}% | "
                    f"Days Held: {days_held}"
                )

    # 最终资金 + 持有股票市值
    if position == 1:
        capital += holdings * stock_data["close"].iloc[-1]

    # 打印交易记录
    for trade in trade_log:
        print(trade)

    print(f"\n💰 Final Capital: {capital:.2f} CNY")


data = get_stock_data('002879', '20250101', '20250314')
calculate_indicators(data)
trade_strategy(data)

# get_board_concept_name_df()
