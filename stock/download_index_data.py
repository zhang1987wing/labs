#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下载上证指数等指数数据
"""

import akshare as ak
import pandas as pd
import os
from datetime import datetime

def download_shanghai_index():
    """下载上证指数数据"""
    print("正在下载上证指数数据...")
    try:
        # 获取上证指数历史数据 (000001.SH)
        sh_index_df = ak.stock_zh_index_daily(symbol="sh000001")
        print(f"上证指数数据量: {len(sh_index_df)}")

        # 保存数据
        sh_index_file = 'data/fundamentals/shanghai_index.csv'
        sh_index_df.to_csv(sh_index_file, index=False, encoding='utf-8-sig')
        print(f"已保存上证指数数据到: {sh_index_file}")

        return True
    except Exception as e:
        print(f"下载上证指数数据失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 开始下载指数数据 ===")

    # 确保数据目录存在
    os.makedirs('data/fundamentals', exist_ok=True)

    # 下载上证指数数据
    sh_success = download_shanghai_index()

    if sh_success:
        print("✅ 指数数据下载完成!")
    else:
        print("❌ 指数数据下载失败，请检查网络连接或数据源")

if __name__ == '__main__':
    main()