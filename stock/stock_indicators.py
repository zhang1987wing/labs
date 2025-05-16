import akshare as ak
import pandas as pd
import talib


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
    df_finance = ak.stock_financial_abstract(symbol=stock_code)
    return df_finance


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


# 预期买入股价
def expected_buy_price(open, close, high, low, highest_250):
    '''
    1、ma5从下往上穿过ma10，且ma5 > ma10
    2、macd金叉发生在macd附近
    3、布林带收盘价大于中线
    4、RSI未超过80
    5、收盘价大于各个均线
    5、均线显示
    '''
    if high == highest_250:
        return round(high * 1.05, 2)


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