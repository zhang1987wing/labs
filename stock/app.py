#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票回测系统 Flask 后端
提供RESTful API接口供前端调用
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import sys
import os
import csv
from datetime import datetime, timedelta
import threading
import uuid

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入自定义模块
import stock_indicators
import stock_trading
from model.stock_holding import stock_holding

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
        
        # 在后台线程中执行回测
        thread = threading.Thread(
            target=run_backtest_thread,
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


def run_backtest_thread(task, params):
    """在后台线程中运行回测"""
    try:
        task.status = 'running'
        task.progress = 10
        
        stock_codes = params['stock_codes']
        initial_capital = float(params['initial_capital'])
        start_date = params['start_date'].replace('-', '')
        end_date = params['end_date'].replace('-', '')
        
        results = []
        total_stocks = len(stock_codes)
        
        for i, stock_code in enumerate(stock_codes):
            try:
                task.progress = 20 + (i / total_stocks) * 70  # 20-90%的进度
                
                # 获取股票数据
                stock_data = stock_indicators.get_daily_stock_data(
                    stock_code, start_date, end_date
                )
                
                if stock_data.empty:
                    results.append({
                        'stock_code': stock_code,
                        'error': '无法获取股票数据'
                    })
                    continue
                
                # 计算技术指标
                stock_indicators.calculate_indicators(stock_data)
                
                # 执行回测
                backtest_result = stock_trading.trade(stock_data, initial_capital, [])
                
                # 格式化结果
                result = format_backtest_result(backtest_result, initial_capital, stock_code)
                results.append(result)
                
            except Exception as e:
                results.append({
                    'stock_code': stock_code,
                    'error': f'回测失败: {str(e)}'
                })
        
        task.progress = 95
        
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


def format_backtest_result(backtest_result, initial_capital, stock_code):
    """格式化回测结果"""
    if hasattr(backtest_result, 'capital'):
        final_capital = backtest_result.capital
        profit = final_capital - initial_capital
        profit_rate = (profit / initial_capital) * 100
        
        return {
            'stock_code': stock_code,
            'initial_capital': initial_capital,
            'final_capital': round(final_capital, 2),
            'profit': round(profit, 2),
            'profit_rate': round(profit_rate, 2),
            'winning_rate': backtest_result.winning_rate,
            'position': backtest_result.state,
            'buy_date': str(backtest_result.buy_date),
            'buy_price': backtest_result.buy_price
        }
    else:
        return {
            'stock_code': stock_code,
            'error': '回测结果格式异常'
        }


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
    """搜索股票代码（从创业板股票列表获取）"""
    keyword = request.args.get('keyword', '').strip()

    # 从CSV文件读取创业板股票数据
    stocks = []
    csv_file_path = os.path.join(os.path.dirname(__file__), '创业板股票列表.csv')

    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                stocks.append({
                    'code': row['股票代码'],
                    'name': row['股票名称']
                })
    except FileNotFoundError:
        return jsonify({'error': '创业板股票列表文件未找到'}), 404
    except Exception as e:
        return jsonify({'error': f'读取股票数据失败: {str(e)}'}), 500

    if keyword:
        filtered_stocks = [
            stock for stock in stocks
            if keyword in stock['code'] or keyword in stock['name']
        ]
    else:
        filtered_stocks = stocks[:20]  # 默认返回前20个

    return jsonify(filtered_stocks)


@app.route('/api/qvix', methods=['GET'])
def get_qvix_index():
    """获取QVIX恐慌指数"""
    try:
        # 从stock_indicators获取真实QVIX数据
        qvix_data = stock_indicators.get_market_qvix_index()

        if qvix_data:
            return jsonify(qvix_data)
        else:
            # 如果获取失败，返回默认数据
            return jsonify({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'qvix_300': 20.33,
                'qvix_1000': 25.79,
                'qvix_cyb': 39.17,
                'qvix_kcb': 46.90,
                'note': '使用默认数据，实时数据获取失败'
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
    
    app.run(debug=True, host='0.0.0.0', port=5000)