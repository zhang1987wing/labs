#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下载QVIX恐慌指数和拥挤度历史数据
保存为CSV文件供基本面分析使用
"""

import akshare as ak
import pandas as pd
import os
from datetime import datetime

def download_qvix_data():
    """下载QVIX恐慌指数数据"""
    print("正在下载QVIX恐慌指数数据...")

    try:
        # 获取创业板ETF期权QVIX历史数据
        cyb_qvix_df = ak.index_option_cyb_qvix()
        print(f"创业板QVIX数据量: {len(cyb_qvix_df)}")

        # 保存创业板QVIX数据
        cyb_qvix_file = 'data/fundamentals/cyb_qvix.csv'
        cyb_qvix_df.to_csv(cyb_qvix_file, index=False, encoding='utf-8-sig')
        print(f"已保存创业板QVIX数据到: {cyb_qvix_file}")

        # 获取沪深300ETF期权QVIX历史数据 (用于上证)
        sh_qvix_df = ak.index_option_300etf_qvix()
        print(f"沪深300QVIX数据量: {len(sh_qvix_df)}")

        # 保存沪深300QVIX数据
        sh_qvix_file = 'data/fundamentals/shanghai_qvix.csv'
        sh_qvix_df.to_csv(sh_qvix_file, index=False, encoding='utf-8-sig')
        print(f"已保存沪深300QVIX数据到: {sh_qvix_file}")

        return True

    except Exception as e:
        print(f"下载QVIX数据失败: {e}")
        return False

def download_congestion_data():
    """下载拥挤度数据"""
    print("正在下载大盘拥挤度数据...")

    try:
        # 获取大盘拥挤度历史数据
        congestion_df = ak.stock_a_congestion_lg()
        print(f"大盘拥挤度数据量: {len(congestion_df)}")

        # 保存拥挤度数据
        congestion_file = 'data/fundamentals/shanghai_congestion.csv'
        congestion_df.to_csv(congestion_file, index=False, encoding='utf-8-sig')
        print(f"已保存大盘拥挤度数据到: {congestion_file}")

        return True

    except Exception as e:
        print(f"下载拥挤度数据失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 开始下载QVIX恐慌指数和拥挤度数据 ===")

    # 确保数据目录存在
    os.makedirs('data/fundamentals', exist_ok=True)

    # 下载QVIX数据
    qvix_success = download_qvix_data()
    print()

    # 下载拥挤度数据
    congestion_success = download_congestion_data()
    print()

    if qvix_success and congestion_success:
        print("✅ 所有数据下载完成!")
    else:
        print("❌ 部分数据下载失败，请检查网络连接或数据源")

if __name__ == '__main__':
    main()