class stock_watching:

    end_date = ''
    reason = ''
    operate = 0

    def __init__(self, stock_code, watching_date, watching_days, watching_price):
        self.stock_code = stock_code
        self.watching_date = watching_date
        self.watching_days = watching_days
        self.watching_price = watching_price

    def __repr__(self):
        action = '买入' if self.operate == 1 else '无'

        return (f"StockCode: {self.stock_code}, 加入日期: {self.watching_date}, "
                f"加入价格: {self.watching_price}, 观察天数: {self.watching_days}, 截止日期: {self.end_date}, "
                f"操作: {action}, 原因: {self.reason}")


if __name__ == '__main__':
    watchlist = [stock_watching('002960', "2023-01-01", 3, 3.11)]

    stock_watching = watchlist[len(watchlist) - 1]
    stock_watching.reason = '321231'
    print(stock_watching)