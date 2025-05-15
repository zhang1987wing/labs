class trade_log:
    def __init__(self, stock_code, price, operation, operate_date, profit, days_held, macd_signal_days, balance):
        self.stock_code = stock_code
        self.price = price
        self.operation = operation
        self.operate_date = operate_date
        self.profit = profit
        self.days_held = days_held
        self.macd_signal_days = macd_signal_days
        self.balance = balance

    def __repr__(self):
        if self.operation == 'BUY':
            return f"BUY: {self.operate_date} at {self.price} | macd_signal_days: {self.macd_signal_days}"
        else:
            return (f"SELL: {self.operate_date} at {self.price} | Profit: {self.profit} | "
                    f"Days Held: {self.days_held} | Balance: {self.balance}")


if __name__ == '__main__':
    trade_log = trade_log('002960', 10.01, "SELL", '2023-01-01',
                          '5.09%', 3, 1, 10000)
    print(trade_log)
