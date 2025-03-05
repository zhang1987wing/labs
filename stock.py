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
    open = df['开盘'].values

    engulfing_pattern = talib.CDLENGULFING(open, high, low, close)
    print(engulfing_pattern)

    return engulfing_pattern


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


data = get_stock_data('002787', '20250225', '20250305')
calculate_indicators(data)

#get_board_concept_name_df()
