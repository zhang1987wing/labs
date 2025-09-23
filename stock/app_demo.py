#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票回测系统 Flask 后端 (演示版)
不依赖talib，提供基本的Web界面演示
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import sys
import os
from datetime import datetime, timedelta
import threading
import uuid
import random
import time

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 存储回测任务状态
backtest_tasks = {}


class BacktestTask:
    def __init__(self, task_id):
        self.task_id = task_id
        self.status = 'pending'  # pending, running, completed, error
        self.progress = 0
        self.result = None
        self.error_message = None
        self.start_time = datetime.now()
        self.end_time = None


@app.route('/')
def index():
    """主页面"""
    return render_template('backtest.html')


@app.route('/api/backtest', methods=['POST'])
def start_backtest():
    """开始回测"""
    try:
        data = request.json
        
        # 验证必需参数
        required_params = ['stock_codes', 'initial_capital', 'start_date', 'end_date']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'缺少必需参数: {param}'}), 400
        
        # 创建任务ID
        task_id = str(uuid.uuid4())
        task = BacktestTask(task_id)
        backtest_tasks[task_id] = task
        
        # 在后台线程中执行模拟回测
        thread = threading.Thread(
            target=run_mock_backtest_thread,
            args=(task, data)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': 'started',
            'message': '回测任务已启动'
        })
        
    except Exception as e:
        return jsonify({'error': f'启动回测失败: {str(e)}'}), 500


def run_mock_backtest_thread(task, params):
    """模拟回测（演示用）"""
    try:
        task.status = 'running'
        task.progress = 10
        time.sleep(1)
        
        stock_codes = params['stock_codes']
        initial_capital = float(params['initial_capital'])
        
        results = []
        total_stocks = len(stock_codes)
        
        for i, stock_code in enumerate(stock_codes):
            task.progress = 20 + (i / total_stocks) * 70  # 20-90%的进度
            time.sleep(random.uniform(1, 3))  # 模拟处理时间
            
            # 模拟回测结果
            profit_rate = random.uniform(-30, 50)  # -30%到50%的收益率
            final_capital = initial_capital * (1 + profit_rate / 100)
            profit = final_capital - initial_capital
            winning_rate = random.uniform(20, 80)
            
            result = {
                'stock_code': stock_code,
                'initial_capital': initial_capital,
                'final_capital': round(final_capital, 2),
                'profit': round(profit, 2),
                'profit_rate': round(profit_rate, 2),
                'winning_rate': round(winning_rate, 1),
                'position': random.choice([0, 1]),
                'buy_date': '2024-03-15',
                'buy_price': round(random.uniform(5, 50), 2)
            }
            results.append(result)
        
        task.progress = 95
        time.sleep(1)
        
        # 计算汇总统计
        summary = calculate_summary_stats(results, initial_capital)
        
        task.result = {
            'individual_results': results,
            'summary': summary,
            'params': params
        }
        task.status = 'completed'
        task.progress = 100
        task.end_time = datetime.now()
        
    except Exception as e:
        task.status = 'error'
        task.error_message = str(e)
        task.end_time = datetime.now()


def calculate_summary_stats(results, initial_capital):
    """计算汇总统计"""
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        return {
            'total_stocks': len(results),
            'successful_stocks': 0,
            'failed_stocks': len(results),
            'total_profit': 0,
            'average_profit_rate': 0,
            'best_stock': None,
            'worst_stock': None
        }
    
    total_profit = sum(r['profit'] for r in valid_results)
    average_profit_rate = sum(r['profit_rate'] for r in valid_results) / len(valid_results)
    
    best_stock = max(valid_results, key=lambda x: x['profit_rate'])
    worst_stock = min(valid_results, key=lambda x: x['profit_rate'])
    
    return {
        'total_stocks': len(results),
        'successful_stocks': len(valid_results),
        'failed_stocks': len(results) - len(valid_results),
        'total_profit': round(total_profit, 2),
        'average_profit_rate': round(average_profit_rate, 2),
        'best_stock': {
            'code': best_stock['stock_code'],
            'profit_rate': best_stock['profit_rate']
        },
        'worst_stock': {
            'code': worst_stock['stock_code'], 
            'profit_rate': worst_stock['profit_rate']
        }
    }


@app.route('/api/backtest/<task_id>', methods=['GET'])
def get_backtest_status(task_id):
    """获取回测任务状态"""
    if task_id not in backtest_tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task = backtest_tasks[task_id]
    
    response = {
        'task_id': task_id,
        'status': task.status,
        'progress': task.progress,
        'start_time': task.start_time.isoformat(),
    }
    
    if task.end_time:
        response['end_time'] = task.end_time.isoformat()
        response['duration'] = (task.end_time - task.start_time).total_seconds()
    
    if task.status == 'completed' and task.result:
        response['result'] = task.result
    elif task.status == 'error':
        response['error'] = task.error_message
    
    return jsonify(response)


@app.route('/api/stock/search', methods=['GET'])
def search_stocks():
    """搜索股票代码"""
    keyword = request.args.get('keyword', '').strip()
    
    # 模拟常用股票代码
    mock_stocks = [
        {'code': '000001', 'name': '平安银行'},
        {'code': '000002', 'name': '万科A'},
        {'code': '600036', 'name': '招商银行'},
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '000858', 'name': '五粮液'},
        {'code': '002415', 'name': '海康威视'},
        {'code': '603103', 'name': '横店影视'},
        {'code': '002748', 'name': '世龙实业'},
        {'code': '002261', 'name': '拓维信息'},
        {'code': '300014', 'name': '亿纬锂能'},
        {'code': '000776', 'name': '广发证券'},
        {'code': '002304', 'name': '洋河股份'},
        {'code': '600887', 'name': '伊利股份'},
        {'code': '000063', 'name': '中兴通讯'},
        {'code': '002142', 'name': '宁波银行'},
    ]
    
    if keyword:
        filtered_stocks = [
            stock for stock in mock_stocks 
            if keyword.lower() in stock['code'].lower() or keyword in stock['name']
        ]
    else:
        filtered_stocks = mock_stocks[:5]  # 默认返回前5个
    
    return jsonify(filtered_stocks)


@app.route('/api/qvix', methods=['GET'])
def get_qvix_index():
    """获取QVIX恐慌指数（模拟数据）"""
    try:
        date_str = request.args.get('date')
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 模拟QVIX数据，基于当前市场情况
        return jsonify({
            'date': date_str,
            'qvix_300': round(random.uniform(15, 25), 2),
            'qvix_1000': round(random.uniform(20, 30), 2),
            'qvix_cyb': round(random.uniform(30, 45), 2),
            'qvix_kcb': round(random.uniform(35, 50), 2)
        })
    except Exception as e:
        return jsonify({'error': f'获取QVIX指数失败: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    # 确保模板和静态文件目录存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🚀 股票回测系统演示版启动中...")
    print("📊 访问地址: http://localhost:5000")
    print("💡 这是演示版本，使用模拟数据进行回测")
    
    app.run(debug=True, host='0.0.0.0', port=5000)