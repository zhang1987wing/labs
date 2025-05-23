class stock_holding:
    def __init__(self, stock_code, capital, winning_rate, state, buy_date, buy_price):
        self.stock_code = stock_code
        self.capital = capital
        self.winning_rate = winning_rate
        self.state = state
        self.buy_date = buy_date
        self.buy_price = buy_price

    def __repr__(self):
        return (f"\nStockCode: {self.stock_code}, Final Capital: {self.capital} CNY, "
                f"Winning Rate: {self.winning_rate}%, 持仓：{self.state}, "
                f"最后一次购买日期为：{self.buy_date}, 买入价格：{self.buy_price}")


if __name__ == '__main__':
    buy_stock = stock_holding('002960', 100000, 0.05, 0, '2023-01-01', 1000)
    print(buy_stock)
