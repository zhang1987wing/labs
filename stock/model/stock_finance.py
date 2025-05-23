class stock_finance:

    report_date = ''

    roe = ''
    total_revenue = ''
    net_profit = ''
    basic_earning_per_share = ''

    yoy_total_revenue = ''
    yoy_net_profit = ''
    yoy_basic_earning_per_share = ''
    yoy_roe = ''

    def __repr__(self):
        return (f"最新财报日期: {self.report_date}, 总收入为: {self.total_revenue}, "
                f"同比: {self.yoy_total_revenue}%; 净利润: {self.net_profit}, 同比: {self.yoy_net_profit}%; "
                f"基本每股收益: {self.basic_earning_per_share}, 同比: {self.yoy_basic_earning_per_share}%; "
                f"净资产收益率: {self.roe}%, 同比: {self.yoy_roe}%;")


if __name__ == '__main__':
    print('123')