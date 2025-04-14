import pandas as pd
import random
import os
from datetime import datetime, timedelta

def generate_mock_data(date_str, stock_list=None, factor_names=None):
    """
    生成 mock 因子数据 DataFrame。
    """
    if stock_list is None:
        stock_list = ['000001', '000002', '000003']
    if factor_names is None:
        factor_names = ['f1', 'f2', 'f3']

    data = []
    for stock in stock_list:
        dynamic_map = {f: round(random.uniform(-1, 1), 4) for f in factor_names}
        row = {
            'timestamp': datetime.strptime(date_str, "%Y-%m-%d"),
            'stock_ticker': stock,
            'core_factor1': round(random.random(), 4),
            'core_factor2': round(random.random(), 4),
            'dynamic_factors': dynamic_map
        }
        data.append(row)

    return pd.DataFrame(data)

def save_mock_data_to_csv(date_str, stock_list=None, factor_names=None, output_dir="data"):
    """
    生成并保存 mock 数据为 CSV 文件。
    """
    df = generate_mock_data(date_str, stock_list, factor_names)
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"factors_{date_str}.csv")
    df.to_csv(file_path, index=False)
    print(f"成功保存 mock 数据：{file_path}")

def save_mock_data_batch(start_date, end_date, stock_list=None, factor_names=None, output_dir="data", skip_weekends=True):
    """
    批量生成并保存多个日期的 mock 数据为 CSV。
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    for i in range((end - start).days + 1):
        current_date = start + timedelta(days=i)
        if skip_weekends and current_date.weekday() >= 5:
            continue
        save_mock_data_to_csv(current_date.strftime('%Y-%m-%d'), stock_list, factor_names, output_dir)

# === 用法示例 ===
if __name__ == "__main__":
    # 单日测试
    save_mock_data_to_csv('2025-04-10')

    # 多日批量测试
    save_mock_data_batch(
        start_date='2025-04-05',
        end_date='2025-04-12',
        stock_list=['000001', '000002'],
        factor_names=['f1', 'f2', 'f3', 'f4'],
        output_dir='data',
        skip_weekends=True
    )
