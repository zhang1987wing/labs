import datetime

import akshare as ak
import pandas as pd
import talib
import numpy as np

from model.stock_finance import stock_finance


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


# 获取日线股票数据
def get_daily_stock_data(stock_code, start_date, end_date):
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


# 获取股票指数数据
def get_daily_index_data(sh_index_code, start_date, end_date):
    print('获取股票数据-begin')
    stock_data = ak.index_zh_a_hist(sh_index_code, 'daily', start_date, end_date)

    print('股票数据-end')
    stock_data.columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅',
                          '涨跌额', '换手率']

    # 将日期转换为索引
    stock_data['日期'] = pd.to_datetime(stock_data['日期'])
    stock_data.set_index('日期', inplace=True)

    return stock_data


# 获取周线股票数据
def get_weekly_stock_data(stock_code, start_date, end_date):
    print('获取股票数据-begin')
    stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="weekly", start_date=start_date, end_date=end_date,
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
    # stock_data["dmi_plus"] = talib.PLUS_DI(high, low, close, timeperiod=14)
    # stock_data["dmi_minus"] = talib.MINUS_DI(high, low, close, timeperiod=14)

    stock_data["dmi_plus"], stock_data["dmi_minus"], stock_data["adx"] = compute_dmi(high, low, close, 14)

    # atr指标
    stock_data["atr"] = talib.ATR(high, low, close, timeperiod=14)

    # rsi指标
    stock_data["rsi"] = talib.RSI(close, timeperiod=14)


# 获取行情板块数据
def get_board_industry_name_df():
    stock_board_industry_name_df = ak.stock_board_industry_name_em()

    # 提取板块名称和涨跌幅
    board_df = stock_board_industry_name_df[['板块名称', '最新价', '涨跌幅']]

    # 按涨跌幅排序
    board_df['涨跌幅'] = board_df['涨跌幅'].astype(str).str.replace('%', '').astype(float)
    board_df = board_df.sort_values(by='涨跌幅', ascending=False)

    return board_df


# 获取行业板块成分股
def get_stock_board_industry_cons_em(symbol):
    stock_board_industry_cons_em_df = ak.stock_board_industry_cons_em(symbol=symbol)

    # 按涨跌幅排序
    stock_board_industry_cons_em_df['涨跌幅'] = stock_board_industry_cons_em_df['涨跌幅'].astype(str).str.replace('%', '').astype(float)
    stock_board_industry_cons_em_df = stock_board_industry_cons_em_df.sort_values(by='涨跌幅', ascending=False)

    return stock_board_industry_cons_em_df


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
def cal_limit_up(prev_price, current_price, stock_code):
    if stock_code.startswith('00') or stock_code.startswith('60'):
        return round(prev_price * 1.10, 2) == current_price
    else:
        return round(prev_price * 1.20, 2) == current_price


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


# 获取QFII持仓，接口报错
def get_stock_report_fund_hold(date):
    stock_report_fund_hold_df = ak.stock_report_fund_hold(symbol="QFII持仓", date=date)
    print(stock_report_fund_hold_df)


# 查询龙虎榜信息
def get_lhb_info(start_date=None):
    # 股票代码前缀
    filter_board_prefixes = ("60", "000", "30")

    '''
    # 机构席位追踪
    stock_lhb_jgstatistic_em_df = ak.stock_lhb_jgstatistic_em(symbol="近一月")
    stock_lhb_jgstatistic_em_df = stock_lhb_jgstatistic_em_df.sort_values(by='名称', ascending=False)
    stock_lhb_jgstatistic_em_filter_df = stock_lhb_jgstatistic_em_df[stock_lhb_jgstatistic_em_df["代码"].str.startswith(filter_board_prefixes)]
    # print(stock_lhb_jgstatistic_em_filter_df)
    '''

    # 个股上榜统计
    stock_lhb_stock_statistic_em_df = ak.stock_lhb_stock_statistic_em(symbol="近一月")
    stock_lhb_stock_statistic_em_df = stock_lhb_stock_statistic_em_df.sort_values(by='最近上榜日', ascending=False)
    stock_lhb_stock_statistic_em_filter_df = stock_lhb_stock_statistic_em_df[stock_lhb_stock_statistic_em_df["代码"].str.startswith(filter_board_prefixes)]

    if start_date:
        lhb_detail_df = ak.stock_lhb_detail_em(start_date=start_date, end_date=start_date)
    else:
        lhb_detail_df = ak.stock_lhb_detail_em()

    if lhb_detail_df.empty:
        print("无龙虎榜数据。")
        return

    # 按照市场总成交额降序排序
    lhb_detail_df = lhb_detail_df.sort_values(by='市场总成交额', ascending=False)

    # 过滤出代码
    lhb_detail_filter_df = lhb_detail_df[lhb_detail_df["代码"].str.startswith(filter_board_prefixes)]

    # 合并同类项
    lhb_detail_filter_merged_df = lhb_detail_filter_df.groupby('代码').agg(stock_name=('代码', 'first'), merged_interpretation=('解读', lambda x: ' | '.join(x))).reset_index()
    lhb_detail_filter_merged_df = lhb_detail_filter_merged_df[['代码', 'merged_interpretation']]

    # 使用 merge 函数连接两个 DataFrame
    # on='stock_code'：指定连接的共同列
    # how='left'：表示保留左侧（df_main）的所有行，并添加匹配的解读内容
    df_final = pd.merge(stock_lhb_stock_statistic_em_filter_df, lhb_detail_filter_merged_df, on='代码', how='left')

    for index, row in df_final.iterrows():
        if row['最近上榜日'].strftime('%Y%m%d') == start_date:
            print(row)

    return df_final

# 内外盘口
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


def compute_dmi(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14):
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)

    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    plus_dm = np.where((high - high.shift(1)) > (low.shift(1) - low),
                       np.maximum(high - high.shift(1), 0), 0)

    minus_dm = np.where((low.shift(1) - low) > (high - high.shift(1)),
                        np.maximum(low.shift(1) - low, 0), 0)

    tr_sum = pd.Series(tr).rolling(window=n).sum()
    plus_dm_sum = pd.Series(plus_dm).rolling(window=n).sum()
    minus_dm_sum = pd.Series(minus_dm).rolling(window=n).sum()

    plus_di = 100 * plus_dm_sum / tr_sum
    minus_di = 100 * minus_dm_sum / tr_sum
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=n).mean()

    return plus_di.values, minus_di.values, adx.values


# 个股每日现金流
def get_individual_fund_flow():
    # 获取资金流数据
    fund_flow_df = ak.stock_fund_flow_individual("即时")

    fund_flow_df["股票代码"] = fund_flow_df["股票代码"].astype(str).str.zfill(6)

    # 查看前几行数据
    # print(fund_flow_df.head())
    return fund_flow_df

# 个股基本信息
def get_stock_individual_info(stock_code):
    individual_info_df = ak.stock_individual_info_em(symbol=stock_code)

    # 查看前几行数据
    # print(individual_info_df.loc[individual_info_df['item'] == '股票代码', 'value'].values[0])
    return individual_info_df


# 概念资金流
def get_stock_fund_flow_concept():
    concept_fund_flow_df = ak.stock_fund_flow_concept(symbol='即时')

    # 查看前几行数据
    # print(individual_info_df.loc[individual_info_df['item'] == '股票代码', 'value'].values[0])
    return concept_fund_flow_df


# 行业资金流
def get_stock_fund_flow_industry():
    industry_fund_flow_df = ak.stock_fund_flow_industry(symbol='即时')

    return industry_fund_flow_df


# 筹码分布
def get_stock_chip(stock_code):
    chip_df = ak.stock_cyq_em(stock_code, 'qfq')
    print(chip_df)

    return chip_df


# 盈利预测
def get_stock_profit_forecast_ths(stock_code):
    stock_profit_forecast_ths_df = ak.stock_profit_forecast_ths(symbol=stock_code,indicator="预测年报每股收益")
    print(stock_profit_forecast_ths_df)


def get_min_stock_data(stock_code, start_date, end_date, minute):
    print('获取股票数据-begin')
    stock_data = ak.stock_zh_a_hist_min_em(symbol=stock_code, period=minute, start_date=start_date, end_date=end_date,
                                    adjust="qfq")
    print('股票数据-end')
    stock_data.columns = ['时间', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅',
                          '涨跌额', '换手率']

    stock_data['股票代码'] = stock_code

    # 将日期转换为索引
    stock_data['时间'] = pd.to_datetime(stock_data['时间'])
    stock_data.set_index('时间', inplace=True)

    return stock_data


def get_monday_weeks_ago(date_str, weeks):
    # 将字符串转换为日期对象
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    # 获取x周前的日期
    delta_days = weeks * 7
    date_34_weeks_ago = date - datetime.timedelta(days=delta_days)

    # 计算当周的周一（weekday: 周一是0）
    weekday = date_34_weeks_ago.weekday()
    monday = date_34_weeks_ago - datetime.timedelta(days=weekday)

    return date.strftime("%Y%m%d"), monday.strftime("%Y%m%d")


def get_day_weekly_macd(daily_df):
    # 重新采样为周K（W-FRI 表示以周五为一周的结束）
    df_weekly = daily_df.resample('W-FRI').agg({
        '开盘': 'first',
        '最高': 'max',
        '最低': 'min',
        '收盘': 'last',
        '成交量': 'sum'
    }).dropna()

    # 检查最后一条原始数据日期
    last_day = daily_df.index[-1]
    last_week_friday = df_weekly.index[-1]
    last_last_week_friday = df_weekly.index[-2]

    if last_week_friday > last_day:
        # 补充最后一周数据（不够一整周也要算）
        df_last_week = daily_df[daily_df.index > last_last_week_friday]
        if not df_last_week.empty:
            new_row = {
                '开盘': df_last_week['开盘'].iloc[0],
                '最高': df_last_week['最高'].max(),
                '最低': df_last_week['最低'].min(),
                '收盘': df_last_week['收盘'].iloc[-1],
                '成交量': df_last_week['成交量'].sum()
            }
            # 添加到 df_weekly，使用最后日期作为索引
            df_weekly = df_weekly.iloc[:-1]
            df_weekly.loc[last_day] = new_row

    # 按时间排序
    df_weekly = df_weekly.sort_index()
    calculate_indicators(df_weekly)
    last_row = df_weekly.iloc[-1]

    weekly_macd_strategy = last_row['macd'] > df_weekly.iloc[-2]['macd']

    return (weekly_macd_strategy and last_row['ma250'] > df_weekly.iloc[-2]['ma250'],
            last_row['ma60'])


def update_stock_code():
    df_sz = ak.stock_info_sz_name_code()

    # 筛选创业板（创业板股票代码以 300 开头）
    df_cyb = df_sz[df_sz['A股代码'].str.startswith('300')]

    # 选择并重命名字段
    df_cyb_export = df_cyb[['A股简称', 'A股代码']].copy()
    df_cyb_export.columns = ['股票名称', '股票代码']

    # 导出为CSV
    df_cyb_export.to_csv("创业板股票列表.csv", index=False, encoding='utf-8')

    print("导出成功，文件名：创业板股票列表.csv")

# 营业收入和主营业务现金流
def get_stock_cash_flow():
     df_cash_flow = ak.stock_cash_flow_sheet_by_report_em()

     return df_cash_flow


# 获取期货数据
def get_futures_hist_em():
     df_futures = ak.get_futures_daily("20250101", "20260101", "CFFEX")

     return df_futures

# 自由现金流估值
def dcf_valuation(fcf_now, growth_rate, discount_rate, terminal_growth, years=5):
    fcf_list = []
    for i in range(1, years + 1):
        fcf = fcf_now * ((1 + growth_rate) ** i)
        fcf_list.append(fcf)

    # 折现每一年的FCF
    discounted_fcf = [fcf / ((1 + discount_rate) ** i) for i, fcf in enumerate(fcf_list, start=1)]

    # 计算终值（Gordon增长模型）并折现
    terminal_value = fcf_list[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    terminal_value_discounted = terminal_value / ((1 + discount_rate) ** years)

    dcf_total = sum(discounted_fcf) + terminal_value_discounted
    return dcf_total


#夏普比率:夏普比率 = (投资组合收益率 - 无风险利率) / 投资组合波动率
def get_sharp_ratio():
    # 假设你已经有了投资组合的每日收益率数据
    # 这里我们创建一个示例 DataFrame
    # 真实数据通常来自于股票、基金或加密货币的历史价格
    dates = pd.date_range(start='2020-01-01', periods=252, freq='B')
    portfolio_returns = pd.Series(np.random.normal(0.0005, 0.01, 252), index=dates)

    # 设置无风险利率
    # 通常使用短期国债收益率，例如1年期国债利率
    # 这里我们假设年化无风险利率为2%
    risk_free_rate = 0.17

    # 将数据转换为DataFrame
    df = pd.DataFrame({'returns': portfolio_returns})

    # 计算每日的平均收益率
    daily_avg_return = df['returns'].mean()

    # 计算每日收益率的标准差（波动率）
    daily_std_dev = df['returns'].std()

    # ---------------------------------------------
    # 下面开始年化数据
    # 通常一年有252个交易日（股票），或365天（加密货币）
    # 这里我们以252个交易日为例
    trading_days_in_year = 252

    # 年化平均收益率
    annualized_avg_return = daily_avg_return * trading_days_in_year

    # 年化波动率
    annualized_std_dev = daily_std_dev * np.sqrt(trading_days_in_year)

    # ---------------------------------------------
    # 计算夏普比率
    # 无风险利率也需要与数据频率匹配
    sharpe_ratio = (annualized_avg_return - risk_free_rate) / annualized_std_dev

    print(f"年化平均收益率: {annualized_avg_return:.4f}")
    print(f"年化波动率: {annualized_std_dev:.4f}")
    print(f"夏普比率: {sharpe_ratio:.4f}")


#未实现盈利值
# 行业指数与万得全A指数的比值


# 获取市场波动率指数，它衡量的是指数在未来30天内的预期波动幅度，以年化的百分比形式呈现。
# 1、关注市场大跌或大涨后的高波动率。（高波动率在30以上）
# 2、对于a股来说，关注长期下跌后或短期上涨后的相对高波动率。（高波动率在25以上），对于创业板或科创板来说，高波动率需要提高上限
def get_market_qvix_index():
    """获取市场QVIX恐慌指数"""
    try:
        # 获取沪深300ETF期权QVIX
        index_option_300etf_qvix_df = ak.index_option_300etf_qvix()
        index_300etf_qvix = index_option_300etf_qvix_df.iloc[-1]

        # 获取中证1000指数期权QVIX
        index_option_1000index_qvix_df = ak.index_option_1000index_qvix()
        index_1000etf_qvix = index_option_1000index_qvix_df.iloc[-1]

        # 获取创业板ETF期权QVIX
        index_option_cyb_qvix_df = ak.index_option_cyb_qvix()
        index_cyb_qvix = index_option_cyb_qvix_df.iloc[-1]

        # 获取科创板50ETF期权QVIX
        index_option_kcb_qvix_df = ak.index_option_kcb_qvix()
        index_kcb_qvix = index_option_kcb_qvix_df.iloc[-1]

        return {
            'date': index_300etf_qvix['date'],
            'qvix_300': float(index_300etf_qvix['close']),
            'qvix_1000': float(index_1000etf_qvix['close']),
            'qvix_cyb': float(index_cyb_qvix['close']),
            'qvix_kcb': float(index_kcb_qvix['close'])
        }
    except Exception as e:
        print(f"获取QVIX数据失败: {e}")
        return None


# 申万一级行业信息
def get_sw_index_first_info():
    sw_index_first_info_df = ak.sw_index_first_info()
    print(sw_index_first_info_df)
    

# 申万三级行业信息
def get_sw_index_third_info():
    sw_index_third_info_df = ak.sw_index_third_info()
    print(sw_index_third_info_df)


# 大盘拥挤度
# 衡量市场微观结构恶化的指标，即成交额排名前5%的个股的成交额占全部A股占比创下历史极值，接近50%，预示着结构恶化，市场行情进入预警区域，或见顶，或风格发生转换。截止到2022年11月，历史上类似的情形出现过5次，市场均发生了巨大的反转，有2次市场进入牛市或维持牛市之中，且市场均发生了风格切换，分别是2008年10月和2015年1月。另三次发生了“牛转熊”现象。
def get_stock_a_congestion_lg():
    """获取大盘拥挤度指标"""
    try:
        stock_a_congestion_lg_df = ak.stock_a_congestion_lg()
        if not stock_a_congestion_lg_df.empty:
            # 获取最新数据
            latest_data = stock_a_congestion_lg_df.iloc[-1]
            return {
                'date': str(latest_data['date']),
                'congestion_rate': float(latest_data['congestion'] * 100),
                'SSE_index': float(latest_data['close']) if 'close' in latest_data else None
            }
        return None
    except Exception as e:
        print(f"获取大盘拥挤度数据失败: {e}")
        return None


# 获取概念板块行情
def get_stock_board_concept_name_em():
    stock_board_concept_name_em_df = ak.stock_board_concept_name_em()

    # 提取板块名称和涨跌幅
    board_df = stock_board_concept_name_em_df[['板块名称', '最新价', '涨跌幅']]

    # 按涨跌幅排序
    board_df['涨跌幅'] = board_df['涨跌幅'].astype(str).str.replace('%', '').astype(float)
    board_df = board_df.sort_values(by='涨跌幅', ascending=False)

    return board_df


# 获取概念板块成分股
def get_stock_board_concept_cons_em(symbol):
    stock_board_concept_cons_em_df = ak.stock_board_concept_cons_em(symbol=symbol)
    return stock_board_concept_cons_em_df

# 获取申万三级行业成分
def get_sw_index_third_cons(symbol):
    sw_index_third_cons_df = ak.sw_index_third_cons(symbol)
    print(sw_index_third_cons_df)


# 获取主板市盈率
def get_stock_market_pe_lg():
    stock_market_pe_lg_df = ak.stock_market_pe_lg(symbol="上证")
    print(stock_market_pe_lg_df)

# 获取主板市净率
# 获取新开户数量
# 万得全A价格指数
# 万得全A利润同比

if __name__ == "__main__":
    # get_lhb_info('20250925')
    # get_stock_a_congestion_lg()
    # print(get_market_qvix_index())
    # get_board_industry_name_df()
    # get_stock_board_concept_name_em()
    # get_stock_board_concept_cons_em('光通信模块')
    # get_sw_index_third_info()
    # get_sw_index_third_cons("850111.SI")
    get_stock_market_pe_lg()