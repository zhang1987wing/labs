import os
from datetime import datetime

import pandas as pd
import concurrent.futures
import csv

import stock_indicators
from stock_holding import stock_holding
from trade_log import trade_log


# 交易日志
def build_trade_log(stock_code, price, operation, operate_date, profit, days_held, macd_signal_days, balance):
    if operation == 'BUY':
        return trade_log(stock_code, price, "BUY", operate_date, 0, 0, macd_signal_days, 0)
    else:
        return trade_log(stock_code, price, "SELL", operate_date, profit, days_held, macd_signal_days, balance)


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

    trade_logs = []
    stock_code = stock_data["股票代码"].iloc[0]
    trade_count = 0
    profit_count = 0
    macd_signal_days = 0

    for i in range(1, len(stock_data)):
        formatted_date = stock_data.index[i].date().strftime('%Y-%m-%d')

        if formatted_date == '2024-02-26':
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

        if dif > dea:
            macd_signal_days = macd_signal_days + 1
        else:
            macd_signal_days = 0

        dmi_strategy = dmi_plus > dmi_minus
        macd_strategy = 0 < macd and macd_signal_days > 0 and dif > -2 and dea > -2 and dif < 0.3 and dea < 0.3
        # macd_strategy = True
        # dmi_strategy = True
        bbands_strategy = True
        ma510_strategy = ma5 >= ma10
        ma20_strategy = ((ma20 > stock_data["ma20"].iloc[i - 1])
                         and (ma20 > stock_data["ma20"].iloc[i - 2])
                         and (stock_data["ma20"].iloc[i - 1] > stock_data["ma20"].iloc[i - 2]))
        ma20_strategy = True
        # ma60_strategy = close > ma60
        heavy_volume_sell_off_strategy = stock_indicators.heavy_volume_sell_off(volume, volume_ma5, open, close, high,
                                                                                low, days_increase)
        # volume_ma5_strategy = False
        # losing_streak = (close < prev_close) and (prev_close < stock_data["收盘"].iloc[i - 2])
        losing_streak = False
        long_upper_shadow_strategy = stock_indicators.long_upper_shadow(open, close, high, low, highest_250)
        # long_upper_shadow_strategy = False
        is_limit_up = stock_indicators.cal_limit_up(prev_close, close)
        # volume,连续3天放量
        volume_last3days = bool((volume > stock_data["成交量"].iloc[i - 1])
                                and (volume > stock_data["成交量"].iloc[i - 2])
                                and (stock_data["成交量"].iloc[i - 1] > stock_data["成交量"].iloc[i - 2]))
        volume_last3days = True
        bbands_buy_strategy = bool(BBANDS_middle > stock_data["BBANDS_middle"].iloc[i - 1] or close > BBANDS_middle)
        bbands_sell_strategy = close < BBANDS_middle
        over_sold_strategy = bool(rsi < 25 and close < BBANDS_lower)
        rsi_strategy = bool(rsi >= 83)

        if heavy_volume_sell_off_strategy and long_upper_shadow_strategy:
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
        '''
        buy_strategy = (position == 0 and macd_strategy and dmi_strategy and ma510_strategy
                        and ma20_strategy and ma60_strategy and volume_last3days)
        '''
        buy_strategy = position == 0 and macd_strategy and dmi_strategy and ma510_strategy and bbands_buy_strategy

        if ((buy_strategy and heavy_volume_sell_off_strategy and long_upper_shadow_strategy) or losing_streak
                or rsi_strategy):
            buy_strategy = False

        if position == 0:
            # 买入条件
            if buy_strategy:
                buy_price = close
                position = 1
                holdings = stock_indicators.get_holdings_cost(capital, buy_price)
                capital -= holdings * buy_price
                buy_date = stock_data.index[i]
                buy_date_idx = i
                trade_logs.append(build_trade_log(stock_code, buy_price, "BUY", buy_date, 0, 0, macd_signal_days, 0))
                atr_sell_price = stock_indicators.sell_price_strategy(high, low, atr)

        # 卖出条件
        else:
            days_held = i - buy_date_idx
            profit_ratio = (close - buy_price) / buy_price
            profit_strategy = profit_ratio < -0.08
            # days_held_strategy = days_held > 5
            atr_strategy = close < atr_sell_price
            # days_increase_strategy = (days_increase <= -5) or (days_increase >= 7.5)
            force_sell_strategy = stock_indicators.force_sell_day(formatted_date)

            '''
            sell_strategy = (profit_strategy or days_held_strategy or atr_strategy or days_increase_strategy
                             or (volume_ma5_strategy and long_upper_shadow_strategy) or losing_streak)
            '''
            sell_strategy = (atr_strategy or bbands_sell_strategy or heavy_volume_sell_off_strategy or profit_strategy
                             or force_sell_strategy)

            if is_limit_up:
                sell_strategy = False

            if sell_strategy:
                sell_price = atr_sell_price if atr_strategy else close
                position = 0
                capital += holdings * sell_price
                holdings = 0
                last_sell_idx = i
                cooldown_days = cooldown_days + 5
                macd_signal_days = 0

                trade_logs.append(build_trade_log(stock_code, f"{sell_price:.2f}", "SELL", stock_data.index[i].date(),
                                                  f"{profit_ratio * 100:.2f}%", days_held, 0, f"{capital:.2f}"))

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
        data = stock_indicators.get_stock_data(stock_code, '20240101', '20250515')

        stock_indicators.calculate_indicators(data)
        buy_stock = trade_strategy(data, base_capital)

        profit = buy_stock.capital - base_capital

        return buy_stock, profit
    except Exception as e:
        print(f"\n{stock_code} 处理失败: {e}")

        return stock_holding(stock_code, round(base_capital, 2), 0, 0, '20240101', round(0, 2)), 0


if __name__ == "__main__":

    today_str = datetime.today().strftime('%Y-%m-%d 00:00:00')
    output_file = "buy_results.csv"
    file_exists = os.path.exists(output_file)

    buy_map = {}
    '''
    stock_profits = get_stock_code()
    '''
    stock_key = '603843'
    stock_profits = {
        stock_key: 0,
        # '002261': 0
    }

    base_capital = 10000

    with open(output_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(['stock_code', 'result'])  # 写入表头

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
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
    # sell_price = stock_indicators.sell_price_strategy(7.4, 6.76, 0.38)
    # print(sell_price)
