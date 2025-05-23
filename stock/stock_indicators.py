import akshare as ak
import pandas as pd
import talib
import numpy as np

from stock.model.stock_finance import stock_finance


def add_stock_code_prefix(stock_code):
    if stock_code.startswith('00'):
        stock_code = f'sz{stock_code}'
    elif stock_code.startswith('30'):
        stock_code = f'sz{stock_code}'
    elif stock_code.startswith('60'):
        stock_code = f'sh{stock_code}'
    else:
        stock_code = f'sh{stock_code}'

    return stock_code

# 获取股票代码
def get_stock_code():
    df = pd.read_csv("stock_codes.csv", dtype={"code": str})  # 替换为你的实际文件名

    # 创建map：key为code，value为0
    code_map = {str(code): 0 for code in df['code']}

    # 输出结果
    return code_map


# 获取股票数据
def get_stock_data(stock_code, start_date, end_date):
    print('获取股票数据-begin')
    stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date,
                                    adjust="qfq")
    print('股票数据-end')
    stock_data.columns = ['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅',
                          '涨跌额', '换手率']

    # 将日期转换为索引
    stock_data['日期'] = pd.to_datetime(stock_data['日期'])
    stock_data.set_index('日期', inplace=True)

    return stock_data


# 指标计算
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
    stock_data['BBANDS_width'] = (
            (stock_data["BBANDS_upper"] - stock_data["BBANDS_middle"]) / stock_data["BBANDS_middle"])

    # 均线指标
    stock_data["ma10"] = np.round(talib.SMA(close, timeperiod=10), 2)
    stock_data["ma5"] = np.round(talib.SMA(close, timeperiod=5), 2)
    stock_data["ma20"] = np.round(talib.SMA(close, timeperiod=20), 2)
    stock_data["ma60"] = np.round(talib.SMA(close, timeperiod=60), 2)
    stock_data["ma250"] = np.round(talib.SMA(close, timeperiod=250), 2)

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

    # rsi指标
    stock_data["rsi"] = talib.RSI(close, timeperiod=14)


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


# 获取某只股票的财务指标
def get_financial_abstract(stock_code):

    stock_fin = stock_finance()

    df_finance = ak.stock_financial_abstract(symbol=stock_code)

    roe, yoy_roe = get_fin_indicator(df_finance, '净资产收益率(ROE)')
    total_revenue, yoy_total_revenue = get_fin_indicator(df_finance, '营业总收入')
    net_profit, yoy_net_profit = get_fin_indicator(df_finance, '净利润')
    basic_earning_per_share, yoy_basic_earning_per_share = get_fin_indicator(df_finance, '基本每股收益')

    stock_fin.roe = roe
    stock_fin.yoy_roe = yoy_roe
    stock_fin.total_revenue = total_revenue
    stock_fin.yoy_total_revenue = yoy_total_revenue
    stock_fin.net_profit = net_profit
    stock_fin.yoy_net_profit = yoy_net_profit
    stock_fin.basic_earning_per_share = basic_earning_per_share
    stock_fin.yoy_basic_earning_per_share = yoy_basic_earning_per_share

    stock_fin.report_date = df_finance.columns[2]

    return stock_fin


def get_fin_indicator(df_finance, indicators_name):
    df_indicator = df_finance[(df_finance['指标'] == indicators_name) & (df_finance['选项'] == '常用指标')]

    latest_date = df_indicator.columns[2]
    prev_date = str(int(latest_date[:4]) - 1) + latest_date[4:]

    # 检查是否存在上一年数据
    if prev_date in df_indicator.columns:
        yoy_finance = ((df_indicator[latest_date] - df_indicator[prev_date]) / abs(df_indicator[prev_date]) * 100).round(2)
    else:
        yoy_finance = None  # 无法计算同比

    return df_indicator[latest_date].iloc[0], yoy_finance.iloc[0]


# 获取东方财富网资讯
def get_news_em(stock_code):
    stock_news_em_df = ak.stock_news_em(symbol=stock_code)

    if stock_news_em_df.empty:
        print(f"{stock_code} 无相关新闻")
        return

    # 将 date 字段转为 datetime 类型并降序排序
    stock_news_em_df['发布时间'] = pd.to_datetime(stock_news_em_df['发布时间'])
    news_df = stock_news_em_df.sort_values(by='发布时间', ascending=False)

    # 取前 10 条
    latest_news = news_df[['发布时间', '新闻标题', '新闻内容']].head(10)

    print(f"\n【{stock_code}】最新新闻（按时间排序）：\n")
    for _, row in latest_news.iterrows():
        print(f"- {row['发布时间'].strftime('%Y-%m-%d %H:%M:%S')} | {row['新闻标题']}\n  摘要：{row['新闻内容']}\n")

    return stock_news_em_df


# 持仓成本
def get_holdings_cost(capital, price):
    shares_per_lot = 100
    max_shares = int(capital // price)

    lots = max_shares // shares_per_lot
    holdings = lots * shares_per_lot

    return holdings


# atr卖出价策略
def sell_price_strategy(high, low, atr):
    height = high - low

    if height <= atr:
        sell_price = low - atr
    elif atr < height < 2 * atr:
        sell_price = low - 1.5 * atr
    else:
        sell_price = low - 2 * atr

    return round(sell_price, 2)


# 是否涨停
def cal_limit_up(prev_price, current_price):
    return round(prev_price * 1.10, 2) == current_price


# 放量大跌，抛盘压力
def heavy_volume_sell_off(volume, avg_volume, open_price, close_price, high_price, low_price, days_increase):
    if high_price == low_price:
        rate = 1
    else:
        rate = abs(close_price - open_price) / (high_price - low_price)

    volume_signal1 = bool(volume > avg_volume * 1.3 and rate > 0.65 and days_increase < 0)
    volume_signal2 = bool(volume > avg_volume * 1.5 and rate > 0.75 and days_increase < 0)
    volume_signal3 = bool(volume > avg_volume * 1.8 and rate > 0.85 and days_increase < 0)

    return volume_signal1 or volume_signal2 or volume_signal3


# 上影线过长
def long_upper_shadow(open, close, high, low, highest_250):
    body = abs(close - open)
    upper_shadow = high - max(close, open)

    if high == highest_250:
        return bool(upper_shadow > body)
    else:
        return bool(upper_shadow > body * 2)


# 强制卖出日（外部情绪抛压极强，不适合任何操作）
def force_sell_day(formatted_date):
    return formatted_date in ['2024-10-08', '2025-04-07']


# 查询龙虎榜信息（默认查询最近一个交易日）
def get_lhb_info(start_date=None):
    if start_date:
        lhb_df = ak.stock_lhb_detail_em(start_date=start_date, end_date=start_date)
    else:
        lhb_df = ak.stock_lhb_detail_em()

    if lhb_df.empty:
        print("无龙虎榜数据。")
        return

    # 按照市场总成交额降序排序
    lhb_df = lhb_df.sort_values(by='市场总成交额', ascending=False)

    # 主板股票代码前缀
    main_board_prefixes = ("60", "000")

    # 过滤出主板代码，并取前 10 条
    lhb_df_main = lhb_df[lhb_df["代码"].str.startswith(main_board_prefixes)]

    # 按股票代码去重，保留第一条记录
    lhb_df_main_unique = lhb_df_main.drop_duplicates(subset="代码", keep="first")

    latest_lhb_df_main_unique = (
        lhb_df_main_unique[['代码', '名称', '收盘价', '涨跌幅', '市场总成交额', '龙虎榜成交额', '换手率', '流通市值']]
        .head(10))

    print(f"\n龙虎榜（市场总成交额）：\n")
    for _, row in latest_lhb_df_main_unique.iterrows():
        print(f"- {row['代码']} | {row['名称']} | {row['收盘价']} | {row['涨跌幅']} | {row['市场总成交额']} "
              f"| {row['龙虎榜成交额']} | {row['换手率']} | {row['流通市值']}\n")


def get_order_book(stock_code):
    symbol = add_stock_code_prefix(stock_code)

    order_book_df = ak.stock_zh_a_tick_tx_js(symbol)

    # 初始化买盘和卖盘列
    order_book_df['买盘'] = 0.0
    order_book_df['卖盘'] = 0.0

    # 分配成交量
    order_book_df.loc[order_book_df['性质'] == '买盘', '买盘'] = order_book_df['成交量']
    order_book_df.loc[order_book_df['性质'] == '卖盘', '卖盘'] = order_book_df['成交量']
    order_book_df.loc[order_book_df['性质'] == '中性盘', ['买盘', '卖盘']] = order_book_df['成交量'] / 2

    # 分组聚合
    grouped = order_book_df.groupby('成交价格')[['买盘', '卖盘']].sum().reset_index()

    # 计算总买盘和总卖盘
    total_buy = grouped['买盘'].sum()
    total_sell = grouped['卖盘'].sum()

    # 添加买卖差值列
    grouped['买卖差'] = grouped['买盘'] - grouped['卖盘']

    # 按买卖差值倒序排序
    grouped_sorted = grouped.sort_values(by='买卖差', ascending=False)

    # 输出结果
    print("按成交价格分组后的数据（按买卖差值倒序）:")
    print(grouped_sorted)

    print(f"\n总买盘: {total_buy}")
    print(f"总卖盘: {total_sell}")

if __name__ == "__main__":
    print(get_financial_abstract('002229'))
    # get_order_book('002229')
