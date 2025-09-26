#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下载A股基本面数据脚本
利用stock_indicators.py中的方法下载各板块数据
"""

import sys
import os
import pandas as pd
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import stock_indicators


def ensure_data_directory():
    """确保数据目录存在"""
    data_dir = 'data/fundamentals'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


def save_data(df, filename, data_dir, description=""):
    """保存数据到CSV文件"""
    if df is not None and not df.empty:
        file_path = os.path.join(data_dir, filename)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"✓ {description}数据已保存: {filename} ({len(df)} 条记录)")
        return True
    else:
        print(f"✗ {description}数据为空，跳过保存")
        return False


def download_all_data():
    """下载所有基本面数据"""
    print("=== A股基本面数据下载工具 ===\n")

    # 确保数据目录存在
    data_dir = ensure_data_directory()
    print(f"数据将保存到: {data_dir}\n")

    success_count = 0
    total_count = 0

    # 1. 下载中证全指数据
    print("1. 获取中证全指(000985)数据...")
    try:
        csi_all_df = stock_indicators.get_index_data(symbol="000985")
        if save_data(csi_all_df, 'csi_all_index.csv', data_dir, "中证全指"):
            success_count += 1
        total_count += 1
    except Exception as e:
        print(f"✗ 获取中证全指数据失败: {e}")
        total_count += 1

    print()

    # 2. 下载创业板指数据
    print("2. 获取创业板指(399006)数据...")
    try:
        cyb_df = stock_indicators.get_index_data(symbol="399006")
        if save_data(cyb_df, 'cyb_index.csv', data_dir, "创业板指"):
            success_count += 1
        total_count += 1
    except Exception as e:
        print(f"✗ 获取创业板指数据失败: {e}")
        total_count += 1

    print()

    # 3. 下载各板块市盈率数据
    pe_boards = [
        ("上证", "shanghai_pe.csv", "上证主板市盈率"),
        ("深证", "shenzhen_pe.csv", "深证主板市盈率"),
        ("创业板", "cyb_pe.csv", "创业板市盈率")
    ]

    for symbol, filename, description in pe_boards:
        print(f"3. 获取{description}数据...")
        try:
            pe_df = stock_indicators.get_stock_market_pe_lg(symbol=symbol)
            if save_data(pe_df, filename, data_dir, description):
                success_count += 1
            total_count += 1
        except Exception as e:
            print(f"✗ 获取{description}失败: {e}")
            total_count += 1

    print()

    # 4. 下载各板块市净率数据
    pb_boards = [
        ("上证", "shanghai_pb.csv", "上证主板市净率"),
        ("深证", "shenzhen_pb.csv", "深证主板市净率"),
        ("创业板", "cyb_pb.csv", "创业板市净率")
    ]

    for symbol, filename, description in pb_boards:
        print(f"4. 获取{description}数据...")
        try:
            pb_df = stock_indicators.get_stock_market_pb_lg(symbol=symbol)
            if save_data(pb_df, filename, data_dir, description):
                success_count += 1
            total_count += 1
        except Exception as e:
            print(f"✗ 获取{description}失败: {e}")
            total_count += 1

    print()

    # 5. 创建数据概要
    create_data_summary(data_dir)

    # 输出结果统计
    print(f"\n=== 下载完成 ===")
    print(f"成功: {success_count}/{total_count} 个文件")
    print(f"数据保存位置: {data_dir}")

    return success_count, total_count


def create_data_summary(data_dir):
    """创建数据概要文件"""
    try:
        print("5. 创建数据概要...")

        summary_data = []
        files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and f != 'data_summary.csv']

        for file in files:
            file_path = os.path.join(data_dir, file)
            try:
                df = pd.read_csv(file_path)

                # 获取数据时间范围
                date_col = None
                for col in ['date', '日期', 'Date']:
                    if col in df.columns:
                        date_col = col
                        break

                if date_col:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    start_date = df[date_col].min().strftime('%Y-%m-%d') if pd.notna(df[date_col].min()) else 'N/A'
                    end_date = df[date_col].max().strftime('%Y-%m-%d') if pd.notna(df[date_col].max()) else 'N/A'
                else:
                    start_date = 'N/A'
                    end_date = 'N/A'

                # 文件描述映射
                descriptions = {
                    'csi_all_index.csv': '中证全指',
                    'cyb_index.csv': '创业板指',
                    'shanghai_pe.csv': '上证主板PE',
                    'shenzhen_pe.csv': '深证主板PE',
                    'cyb_pe.csv': '创业板PE',
                    'shanghai_pb.csv': '上证主板PB',
                    'shenzhen_pb.csv': '深证主板PB',
                    'cyb_pb.csv': '创业板PB'
                }

                summary_data.append({
                    'filename': file,
                    'description': descriptions.get(file, file),
                    'records': len(df),
                    'start_date': start_date,
                    'end_date': end_date,
                    'columns_count': len(df.columns),
                    'file_size_kb': round(os.path.getsize(file_path) / 1024, 2)
                })

            except Exception as e:
                summary_data.append({
                    'filename': file,
                    'description': 'Error',
                    'records': 0,
                    'start_date': 'Error',
                    'end_date': 'Error',
                    'columns_count': 0,
                    'file_size_kb': 0,
                    'error': str(e)[:100]
                })

        # 保存概要
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_file = os.path.join(data_dir, 'data_summary.csv')
            summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')

            print(f"✓ 数据概要已生成: data_summary.csv")
            print("\n=== 数据文件概要 ===")
            for _, row in summary_df.iterrows():
                print(f"{row['description']}: {row['records']} 条记录 "
                      f"({row['start_date']} 至 {row['end_date']}) "
                      f"[{row['file_size_kb']} KB]")

    except Exception as e:
        print(f"✗ 生成数据概要失败: {e}")


def check_data_availability():
    """检查数据是否存在"""
    data_dir = 'data/fundamentals'
    if not os.path.exists(data_dir):
        return False, "数据目录不存在"

    required_files = [
        'csi_all_index.csv',
        'cyb_index.csv',
        'shanghai_pe.csv',
        'shanghai_pb.csv',
        'shenzhen_pe.csv',
        'shenzhen_pb.csv',
        'cyb_pe.csv',
        'cyb_pb.csv'
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(data_dir, file)):
            missing_files.append(file)

    if missing_files:
        return False, f"缺少文件: {', '.join(missing_files)}"

    return True, "数据完整"


if __name__ == "__main__":
    # 检查是否已有数据
    has_data, status = check_data_availability()

    if has_data:
        print("发现已有数据文件。")
        choice = input("是否重新下载? (y/n): ").lower().strip()
        if choice != 'y':
            print("跳过下载。")
            exit(0)

    # 开始下载数据
    success, total = download_all_data()

    if success == total:
        print("\n🎉 所有数据下载成功!")
    elif success > 0:
        print(f"\n⚠️  部分数据下载成功 ({success}/{total})")
    else:
        print("\n❌ 数据下载失败")

    print("\n下一步: 创建前端页面展示这些数据")