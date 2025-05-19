class stock_watching:

    end_date = ''
    reason = ''

    def __init__(self, stock_code, watching_date, watching_days, watching_price):
        self.stock_code = stock_code
        self.watching_date = watching_date
        self.watching_days = watching_days
        self.watching_price = watching_price

    def __repr__(self):
        return (f"StockCode: {self.stock_code}, 加入日期: {self.watching_date}, "
                f"加入价格: {self.watching_price}, 观察天数: {self.watching_days}, 截止日期为: {self.end_date}, "
                f"原因: {self.reason}")


if __name__ == '__main__':
    stock_watching = stock_watching('002960', "2023-01-01", 3, 3.11)
    stock_watching.end_date = '2025-05-15'
    stock_watching.reason = '12312312'
    print(stock_watching)