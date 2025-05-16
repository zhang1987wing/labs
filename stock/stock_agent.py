import akshare as ak
import pandas as pd
import numpy as np
import talib
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, LSTM

# 获取历史数据
stock_data = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20220101", end_date="20250423", adjust="qfq")

close = stock_data['收盘'].values
high = stock_data['最高'].values
low = stock_data['最低'].values
open = stock_data['开盘'].values
volume = stock_data['成交量'].values.astype(float)

highest_250 = talib.MAX(high, timeperiod=250)
stock_data["highest_250"] = highest_250

# 均线指标
stock_data["ma10"] = talib.SMA(close, timeperiod=10).round(2)
stock_data["ma5"] = talib.SMA(close, timeperiod=5).round(2)
stock_data["ma20"] = talib.SMA(close, timeperiod=20).round(2)
stock_data["ma60"] = talib.SMA(close, timeperiod=60).round(2)
stock_data["ma250"] = talib.SMA(close, timeperiod=250).round(2)

# 平均交易量
stock_data["volume_ma5"] = talib.SMA(volume, timeperiod=5)

# MACD指标
stock_data["macd_dif"], stock_data["macd_dea"], MACD = talib.MACD(close, fastperiod=12, slowperiod=26,
                                                                      signalperiod=9)
stock_data["macd"] = (stock_data["macd_dif"] - stock_data["macd_dea"]) * 2

# DMI指标
stock_data["dmi_plus"] = talib.PLUS_DI(high, low, close, timeperiod=14)
stock_data["dmi_minus"] = talib.MINUS_DI(high, low, close, timeperiod=14)

# 标准化
features = ['收盘', 'ma5', 'ma10', 'macd']
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(stock_data[features])

# 准备训练数据
sequence_length = 60
x, y = [], []
for i in range(sequence_length, len(scaled_data)):
    x.append(scaled_data[i-sequence_length:i, 0])
    y.append(scaled_data[i, 0])
x, y = np.array(x), np.array(y)
x = np.reshape(x, (x.shape[0], x.shape[1], 1))

# 构建LSTM模型
model = Sequential()
model.add(LSTM(units=64, return_sequences=False, input_shape=(x.shape[1], x.shape[2])))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mean_squared_error')
model.fit(x, y, epochs=10, batch_size=32)

# 预测未来1天
last_60_days = scaled_data[-60:]
last_60_days = np.reshape(last_60_days, (-1, 60, 1))
predicted_scaled_price = model.predict(last_60_days)

dummy_input = np.zeros((predicted_scaled_price.shape[0], 4))
dummy_input[:, 0] = predicted_scaled_price[:, 0]  # 假设 close 在第4列

inversed = scaler.inverse_transform(dummy_input)
predicted_price = inversed[:, 3]

print(f"预测下一交易日收盘价：{predicted_price[0]:.2f} 元")
