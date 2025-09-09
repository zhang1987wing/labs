import os
import random
import time
from datetime import datetime

import concurrent.futures
import csv

import stock_indicators
from stock.model.stock_holding import stock_holding
from stock.model.trade_log import trade_log


# 交易日志
def build_trade_log(stock_code, price, operation, operate_date, profit, days_held, macd_signal_days, balance):
    if operation == 'BUY':
        return trade_log(stock_code, price, "BUY", operate_date, 0, 0, macd_signal_days, 0)
    else:
        return trade_log(stock_code, price, "SELL", operate_date, profit, days_held, macd_signal_days, balance)


def buy_watchlist_strategy(stock_watchlist, today):

    for stock_watch in stock_watchlist:
        if stock_watch.end_date == today and stock_watch.operate == 1:
            return True

    return False


def is_buying(daily_date, min_buying_point):
    for point in min_buying_point:
        formatted_date = point.operate_date.strftime('%Y-%m-%d')

        if daily_date == formatted_date:
            return True, point.price

    return False, 0

'''
# 日K维度
# 股价越高，短期内rsi高点越低出现背驰，不买入
# 从高点下来，向下趋势，买入点未到前一上升趋势的最低点，后期的反弹未形成更高的低点，则不参与买入
# 从高点下来，向下趋势，买入点未到前一上升趋势的最低点，后期的盘整未形成更高的低点，则不参与买入
# 从高点下来，向下趋势，买入点未到前一上升趋势的最低点，年线向下，不买入
# 从高点下来，向下趋势，买入点已经是最低点，观察点，0线下的macd交叉点离0线越近，才能买入
# 从高点下来，向下趋势，周线未有金叉，不买入
# 从低点上去，向上趋势，如果买入点为第一买点的高点，其后的回撤，macd依旧在0线以上，观察30分钟的走势
# 从低点上去，盘整趋势，买入点需要在最低点附近
'''
def get_buy_strategy(indicators_map, cooldown_days):
    open_price = indicators_map.get("open_price")
    close_price = indicators_map.get("close_price")
    prev_close_price = indicators_map.get("prev_close_price")
    high_price = indicators_map.get("high_price")
    highest_250 = indicators_map.get("highest_250")
    low_price = indicators_map.get("low_price")
    volume = indicators_map.get("volume")
    days_increase = indicators_map.get("days_increase")
    BBANDS_lower = indicators_map.get("BBANDS_lower")
    BBANDS_middle = indicators_map.get("BBANDS_middle")
    prev_BBANDS_middle = indicators_map.get("prev_BBANDS_middle")
    ma5 = indicators_map.get("ma5")
    ma10 = indicators_map.get("ma10")
    macd = indicators_map.get("macd")
    prev_macd = indicators_map.get("prev_macd")
    dmi_plus = indicators_map.get("dmi_plus")
    dmi_minus = indicators_map.get("dmi_minus")

    volume_ma5 = indicators_map.get("volume_ma5")
    rsi = indicators_map.get("open_price")

    dmi_buy_strategy = dmi_plus > dmi_minus
    macd_buy_strategy = 0 < macd and macd > prev_macd

    ma510_buy_strategy = ma5 >= ma10

    heavy_volume_sell_off_strategy = stock_indicators.heavy_volume_sell_off(volume, volume_ma5, open_price, close_price,
                                                                            high_price,
                                                                            low_price, days_increase)
    long_upper_shadow_strategy = stock_indicators.long_upper_shadow(open_price, close_price, high_price, low_price,
                                                                    highest_250)

    bbands_buy_strategy = bool(BBANDS_middle > prev_BBANDS_middle or close_price > BBANDS_middle)
    over_sold_strategy = bool(rsi < 25 and close_price < BBANDS_lower)
    rsi_strategy = bool(rsi >= 83)

    if heavy_volume_sell_off_strategy and long_upper_shadow_strategy:
        cooldown_days = cooldown_days + 2

    buy_strategy = macd_buy_strategy and dmi_buy_strategy and ma510_buy_strategy and bbands_buy_strategy

    if (buy_strategy and heavy_volume_sell_off_strategy and long_upper_shadow_strategy) or rsi_strategy:
        buy_strategy = False

    return buy_strategy, cooldown_days


def get_sell_strategy(indicators_map, formatted_date):
    close_price = indicators_map.get("close_price")
    prev_close_price = indicators_map.get("prev_close_price")
    BBANDS_middle = indicators_map.get("BBANDS_middle")
    atr_sell_price = indicators_map.get("atr_sell_price")
    volume = indicators_map.get("volume")
    volume_ma5 = indicators_map.get("volume_ma5")
    open_price = indicators_map.get("open_price")
    high_price = indicators_map.get("high_price")
    low_price = indicators_map.get("low_price")
    days_increase = indicators_map.get("days_increase")
    stock_code = indicators_map.get("stock_code")

    profit_strategy = False
    atr_strategy = close_price < atr_sell_price
    force_sell_strategy = stock_indicators.force_sell_day(formatted_date)
    bbands_sell_strategy = close_price < BBANDS_middle

    heavy_volume_sell_off_strategy = stock_indicators.heavy_volume_sell_off(volume, volume_ma5, open_price, close_price,
                                                                            high_price,
                                                                            low_price, days_increase)

    is_limit_up = stock_indicators.cal_limit_up(prev_close_price, close_price, stock_code)

    sell_strategy = (atr_strategy or bbands_sell_strategy or profit_strategy or heavy_volume_sell_off_strategy
                     or force_sell_strategy)

    if is_limit_up:
        sell_strategy = False

    sell_price = atr_sell_price if atr_strategy else close_price

    return sell_strategy, sell_price

def trade(stock_data, capital, min_buying_point):
    buy_date = ''
    position = 0  # 持仓状态 (0: 空仓, 1: 持仓)
    buy_price = 0
    # capital = 100000  # 初始资金
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

    indicators_map = {}

    # watchlist = stock_watchlist.func_ma5_golden_cross_strategy(stock_data)

    for i in range(1, len(stock_data)):
        formatted_date = stock_data.index[i].date().strftime('%Y-%m-%d')

        if formatted_date < '2021-01-01':
            continue

        if formatted_date == '2023-01-30':
            print("debug")

        indicators_map["stock_code"] = stock_code
        indicators_map["open_price"] = stock_data["开盘"].iloc[i]
        indicators_map["close_price"] = stock_data["收盘"].iloc[i]
        indicators_map["prev_close_price"] = stock_data["收盘"].iloc[i - 1]
        indicators_map["high_price"] = stock_data["最高"].iloc[i]
        indicators_map["highest_250"] = stock_data["highest_250"].iloc[i]
        indicators_map["low_price"] = stock_data["最低"].iloc[i]
        indicators_map["volume"] = stock_data["成交量"].iloc[i]
        indicators_map["days_increase"] = stock_data["涨跌幅"].iloc[i]
        indicators_map["BBANDS_middle"] = stock_data["BBANDS_middle"].iloc[i]
        indicators_map["prev_BBANDS_middle"] = stock_data["BBANDS_middle"].iloc[i - 1]
        indicators_map["BBANDS_lower"] = stock_data["BBANDS_lower"].iloc[i]
        indicators_map["BBANDS_width"] = stock_data["BBANDS_width"].iloc[i]
        indicators_map["ma5"] = stock_data["ma5"].iloc[i]
        indicators_map["ma10"] = stock_data["ma10"].iloc[i]
        indicators_map["ma20"] = stock_data["ma20"].iloc[i]
        indicators_map["ma60"] = stock_data["ma60"].iloc[i]
        indicators_map["ma250"] = stock_data["ma250"].iloc[i]
        indicators_map["macd"] = stock_data["macd"].iloc[i]
        indicators_map["prev_macd"] = stock_data["macd"].iloc[i - 1]
        indicators_map["dif"] = stock_data["macd_dif"].iloc[i]
        indicators_map["dea"] = stock_data["macd_dea"].iloc[i]
        indicators_map["dmi_plus"] = stock_data["dmi_plus"].iloc[i]
        indicators_map["dmi_minus"] = stock_data["dmi_minus"].iloc[i]
        indicators_map["atr"] = stock_data["atr"].iloc[i]
        indicators_map["volume_ma5"] = stock_data["volume_ma5"].iloc[i]
        indicators_map["rsi"] = stock_data["rsi"].iloc[i]
        indicators_map["index"] = stock_data.index
        indicators_map["prev_index"] = stock_data.index[i]

        # buy_strategy = buy_watchlist_strategy(watchlist, formatted_date)

        if position == 0:
            # 获取周线数据
            '''
            weekly_macd, weekly_ma60 = stock_indicators.get_day_weekly_macd(
                stock_data[stock_data.index <= stock_data.index[i]])
            weekly_strategy = weekly_macd and indicators_map["close_price"] > weekly_ma60
            '''
            weekly_strategy = True
            common_buy_strategy, cooldown_days = get_buy_strategy(indicators_map, cooldown_days)
            buy_strategy = common_buy_strategy and weekly_strategy

            # 符合30分钟买点，则买入
            # buy_strategy, buy_price = is_buying(formatted_date, min_buying_point)

            if cooldown_days > 0:
                cooldown_days = cooldown_days - 1
                continue

            # 买入条件
            if buy_strategy:

                buy_price = indicators_map.get('close_price')
                position = 1
                holdings = stock_indicators.get_holdings_cost(capital, buy_price)
                capital -= holdings * buy_price
                buy_date = stock_data.index[i]
                buy_date_idx = i
                trade_logs.append(build_trade_log(stock_code, buy_price, "BUY", buy_date, 0, 0, macd_signal_days, 0))
                atr_sell_price = stock_indicators.sell_price_strategy(indicators_map.get('high_price'),
                                                                      indicators_map.get('low_price'),
                                                                      indicators_map.get('atr'))
                indicators_map["atr_sell_price"] = atr_sell_price
                indicators_map["buy_price"] = buy_price

        # 卖出条件
        else:
            days_held = i - buy_date_idx
            profit_ratio = (indicators_map.get('close_price') - buy_price) / buy_price

            sell_strategy, sell_price = get_sell_strategy(indicators_map, formatted_date)

            if sell_strategy:
                position = 0
                capital += holdings * sell_price
                holdings = 0
                last_sell_idx = i
                cooldown_days = cooldown_days + 5
                macd_signal_days = 0

                trade_logs.append(build_trade_log(stock_code, f"{sell_price:.2f}", "SELL", stock_data.index[i].date(),
                                                  f"{profit_ratio * 100:.2f}", days_held, 0, f"{capital:.2f}"))

                trade_count = trade_count + 1

                if profit_ratio > 0:
                    profit_count = profit_count + 1

    # 最终资金 + 持有股票市值
    if position == 1:
        capital += holdings * stock_data["收盘"].iloc[-1]

    if capital < 0:
        capital = 0

    # 打印交易记录
    for trade_log in trade_logs:
        print(trade_log)

    if trade_count == 0:
        winning_rate = 0
    else:
        winning_rate = round(profit_count / trade_count * 100, 2)

    buy_stock = stock_holding(stock_code, round(capital, 2), winning_rate, position, buy_date, round(buy_price, 2))

    print(buy_stock)
    return buy_stock


def get_30min_buying_point(stock_code):
    stock_data = stock_indicators.get_min_stock_data(stock_code, '20210101', '20250718', 30)
    stock_indicators.calculate_indicators(stock_data)

    buy_date = ''
    position = 0  # 持仓状态 (0: 空仓, 1: 持仓)
    buy_price = 0
    holdings = 0
    atr_sell_price = 0.0
    cooldown_days = 0

    trade_logs = []
    stock_code = stock_data["股票代码"].iloc[0]
    trade_count = 0
    profit_count = 0
    macd_signal_days = 0

    indicators_map = {}

    for i in range(1, len(stock_data)):
        formatted_date = stock_data.index[i].date().strftime('%Y-%m-%d')

        if formatted_date < '2021-01-01':
            continue

        if formatted_date == '2023-01-30':
            print("debug")

        indicators_map["open_price"] = stock_data["开盘"].iloc[i]
        indicators_map["close_price"] = stock_data["收盘"].iloc[i]
        indicators_map["prev_close_price"] = stock_data["收盘"].iloc[i - 1]
        indicators_map["high_price"] = stock_data["最高"].iloc[i]
        indicators_map["highest_250"] = stock_data["highest_250"].iloc[i]
        indicators_map["low_price"] = stock_data["最低"].iloc[i]
        indicators_map["volume"] = stock_data["成交量"].iloc[i]
        indicators_map["days_increase"] = stock_data["涨跌幅"].iloc[i]
        indicators_map["BBANDS_middle"] = stock_data["BBANDS_middle"].iloc[i]
        indicators_map["prev_BBANDS_middle"] = stock_data["BBANDS_middle"].iloc[i - 1]
        indicators_map["BBANDS_lower"] = stock_data["BBANDS_lower"].iloc[i]
        indicators_map["BBANDS_width"] = stock_data["BBANDS_width"].iloc[i]
        indicators_map["ma5"] = stock_data["ma5"].iloc[i]
        indicators_map["ma10"] = stock_data["ma10"].iloc[i]
        indicators_map["ma20"] = stock_data["ma20"].iloc[i]
        indicators_map["ma60"] = stock_data["ma60"].iloc[i]
        indicators_map["ma250"] = stock_data["ma250"].iloc[i]
        indicators_map["macd"] = stock_data["macd"].iloc[i]
        indicators_map["prev_macd"] = stock_data["macd"].iloc[i - 1]
        indicators_map["dif"] = stock_data["macd_dif"].iloc[i]
        indicators_map["dea"] = stock_data["macd_dea"].iloc[i]
        indicators_map["dmi_plus"] = stock_data["dmi_plus"].iloc[i]
        indicators_map["dmi_minus"] = stock_data["dmi_minus"].iloc[i]
        indicators_map["atr"] = stock_data["atr"].iloc[i]
        indicators_map["volume_ma5"] = stock_data["volume_ma5"].iloc[i]
        indicators_map["rsi"] = stock_data["rsi"].iloc[i]
        indicators_map["index"] = stock_data.index
        indicators_map["prev_index"] = stock_data.index[i]

        if position == 0:
            buy_strategy, cooldown_days = get_buy_strategy(indicators_map, cooldown_days)

            if cooldown_days > 0:
                cooldown_days = cooldown_days - 1
                continue

            # 买入条件
            if buy_strategy:

                buy_price = indicators_map.get('close_price')
                position = 1
                buy_date = stock_data.index[i]
                trade_logs.append(build_trade_log(stock_code, buy_price, "BUY", buy_date, 0, 0, macd_signal_days, 0))
                atr_sell_price = stock_indicators.sell_price_strategy(indicators_map.get('high_price'),
                                                                      indicators_map.get('low_price'),
                                                                      indicators_map.get('atr'))
                indicators_map["atr_sell_price"] = atr_sell_price
                indicators_map["buy_price"] = buy_price

        # 卖出条件
        else:
            profit_ratio = (indicators_map.get('close_price') - buy_price) / buy_price
            sell_strategy, sell_price = get_sell_strategy(indicators_map, formatted_date)

            if sell_strategy:
                position = 0
                cooldown_days = cooldown_days + 5
                macd_signal_days = 0

                trade_count = trade_count + 1

                if profit_ratio > 0:
                    profit_count = profit_count + 1

    '''
    # 打印交易记录
    for trade_log in trade_logs:
        print(trade_log)
    '''
    return trade_logs


def cal_profit_to_loss_ratio(stocks_profits, initial_funds):
    # 计算所有股票的盈亏总和
    total_profit_loss = sum(stocks_profits.values())

    # 计算整体盈亏比
    profit_ratio = total_profit_loss / initial_funds

    result_str = f"\n总盈亏：{total_profit_loss:.2f}, 整体盈亏比: {profit_ratio * 100:.2f}%"
    print(result_str)

    return result_str


def process_stock(stock_code, base_capital):
    try:
        time.sleep(random.uniform(1, 3.0))
        data = stock_indicators.get_daily_stock_data(stock_code, '20120101', '20250909')

        # min_buying_point = get_30min_buying_point(stock_code)
        min_buying_point = []
        stock_indicators.calculate_indicators(data)
        buy_stock = trade(data, base_capital, min_buying_point)

        profit = buy_stock.capital - base_capital

        return buy_stock, profit
    except Exception as e:
        print(f"\n{stock_code} 处理失败: {e}")

        return stock_holding(stock_code, round(base_capital, 2), 0, 0, '19000101', round(0, 2)), 0


if __name__ == "__main__":

    today_str = datetime.today().strftime('%Y-%m-%d 00:00:00')
    output_file = "buy_results.csv"
    file_exists = os.path.exists(output_file)

    buy_map = {}
    '''
    stock_profits = stock_indicators.get_stock_code()
    '''
    stock_key = '002261'
    stock_profits = {
        stock_key: 0,
        # '002261': 0
    }

    base_capital = 10000

    with open(output_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(['stock_code', 'result'])  # 写入表头

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(process_stock, code, base_capital): code for code in stock_profits.keys()}

            for future in concurrent.futures.as_completed(futures):
                buy_stock, profit = future.result()

                stock_profits[buy_stock.stock_code] = profit
                if str(buy_stock.buy_date) == today_str:
                    buy_map[buy_stock.stock_code] = buy_stock

                if buy_stock.capital == 0:
                    result_str = f"{buy_stock.stock_code} 模拟交易失败"
                    print(result_str)

                    writer.writerow([buy_stock.stock_code, result_str])

                writer.writerow([buy_stock.stock_code, buy_stock])  # 写入一行记录

            writer.writerow(['000000', cal_profit_to_loss_ratio(stock_profits, base_capital)])

    print(f'\n今天可以购买的股票总量为：{len(buy_map)}')
    print(buy_map)

    # get_news_em(stock_key)

    # get_lhb_info('20250514')

    # stock_data = ak.stock_zh_a_hist(symbol='002261', period="daily", start_date='20240101', end_date='20250506',
    #                                 adjust="qfq")
    # print(stock_data)
    # 业绩报表
    # data = ak.stock_yjbb_em(date="20240930")

    # print(data.head())

    # 筹码分布
    # data = ak.stock_cyq_em('000796', adjust="qfq")
    # print(data)

    # get_board_concept_name_df()
    # sell_price = stock_indicators.sell_price_strategy(13.47, 12.6, 0.42)
    # print(sell_price)