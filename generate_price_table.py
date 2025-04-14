import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_price_table(start_date='2025-04-01', end_date='2025-04-15', stock_list=None, seed=42):
    if stock_list is None:
        stock_list = ['000001', '000002', '000003']

    np.random.seed(seed)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # B: business days
    data = []

    for stock in stock_list:
        base_price = np.random.uniform(10, 50)  # 随机起始价
        drift = np.random.uniform(-0.01, 0.01)  # 总体趋势
        prices = [base_price]
        for _ in range(1, len(dates)):
            shock = np.random.normal(loc=drift, scale=0.01)
            new_price = prices[-1] * (1 + shock)
            prices.append(max(new_price, 0.5))  # 避免负价格
        for date, price in zip(dates, prices):
            data.append({
                'stock_ticker': stock,
                'timestamp': date.strftime('%Y-%m-%d'),
                'close_price': round(price, 4)
            })

    df_price = pd.DataFrame(data)
    return df_price


if __name__ == '__main__':
    df = generate_price_table()
    print(df.head())
    df.to_csv("simulated_price_table.csv", index=False)
    print("已保存模拟价格数据表到 simulated_price_table.csv")