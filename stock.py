import akshare as ak
import numpy as np
import pandas as pd
import talib


def get_stock_data(stock_code, start_date, end_date):
    data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
    print(data)
    return data


def calculate_indicators(df):
    close = df['收盘'].values
    high = df['最高'].values
    low = df['最低'].values

    df['MA20'] = talib.SMA(close, timeperiod=20)
    DIF, DEA, MACD = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    df['DIF'] = DIF
    df['DEA'] = DEA
    df['MACD'] = (DIF - DEA) * 2
    df['RSI'] = talib.RSI(close, timeperiod=14)

    print(MACD > 0 and DIF >= DEA)
    #print(80 <= df['RSI'] <= 20)

    # 计算 DMI 指标
    period = 14  # 常用周期为14

    # +DI 和 -DI
    plus_di = talib.PLUS_DI(high, low, close, timeperiod=period)
    minus_di = talib.MINUS_DI(high, low, close, timeperiod=period)

    # ADX（平均趋向指数）
    adx = talib.ADX(high, low, close, timeperiod=period)

    # 输出结果
    print("Plus DI (+DI):", plus_di)
    print("Minus DI (-DI):", minus_di)
    print(plus_di > minus_di)

    return df


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


#data = get_stock_data('002215', '20240224', '20250224')
#calculate_indicators(data)

get_board_concept_name_df()
