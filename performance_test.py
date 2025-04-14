# performance_test.py

import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from generate_data import generate_mock_data
from upload_data import upload_dataframe, upload_batch_dataframe
from load_factor_data import load_factor_data
from config import CLICKHOUSE_URL, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD

results = []  # 用于记录结果

# 写入性能测试

def test_write_performance(date_str, stock_count, factor_count, overwrite=True):
    stock_list = [f"{i:06d}" for i in range(1, stock_count + 1)]
    factor_names = [f"f{i}" for i in range(1, factor_count + 1)]
    
    df = generate_mock_data(date_str, stock_list, factor_names)

    start = time.time()
    upload_dataframe(df, overwrite=overwrite)
    duration = round(time.time() - start, 2)

    print(f"写入测试 | 股票数: {stock_count} | 因子数: {factor_count} | 耗时: {duration} 秒")
    results.append({
        "type": "write",
        "date": date_str,
        "stocks": stock_count,
        "factors": factor_count,
        "duration_sec": duration
    })

# 读取性能测试（支持是否压缩）

def test_read_performance(date_str, enable_compression=True):
    start = time.time()
    df = load_factor_data(
        date_str=date_str,
        clickhouse_url=CLICKHOUSE_URL,
        username=CLICKHOUSE_USERNAME,
        password=CLICKHOUSE_PASSWORD,
        enable_compression=enable_compression
    )
    duration = round(time.time() - start, 2)
    print(f"读取测试 | 日期: {date_str} | 记录数: {len(df)} | 压缩: {enable_compression} | 耗时: {duration} 秒")
    results.append({
        "type": "read_compressed" if enable_compression else "read_uncompressed",
        "date": date_str,
        "stocks": len(df),
        "factors": len(df.columns) - 3,
        "duration_sec": duration
    })

# 批量上传测试

def test_batch_upload(start_date, end_date, stock_count, factor_count, skip_weekends=False):
    stock_list = [f"{i:06d}" for i in range(1, stock_count + 1)]
    factor_names = [f"f{i}" for i in range(1, factor_count + 1)]

    start = time.time()
    upload_batch_dataframe(
        start_date=start_date,
        end_date=end_date,
        stock_list=stock_list,
        factor_names=factor_names,
        overwrite=True,
        skip_weekends=skip_weekends
    )
    duration = round(time.time() - start, 2)
    print(f"批量上传测试 | {start_date} ~ {end_date} | 股票数: {stock_count} | 因子数: {factor_count} | 耗时: {duration} 秒")
    results.append({
        "type": "batch_write",
        "date": f"{start_date}~{end_date}",
        "stocks": stock_count,
        "factors": factor_count,
        "duration_sec": duration
    })

# 批量测试组合

def run_all_tests():
    test_cases = [
        ("2025-04-11", 100, 5),
        ("2025-04-12", 1000, 10),
        ("2025-04-13", 5000, 20),
        ("2025-04-14", 10000, 30),
        ("2025-04-15", 25000, 40),  # stress case级别测试一周数据
    ]

    print("=== 写入性能测试 ===")
    for date_str, stock_cnt, factor_cnt in test_cases:
        test_write_performance(date_str, stock_cnt, factor_cnt, overwrite=True)

    print("\n=== 读取性能测试（启用压缩） ===")
    for date_str, _, _ in test_cases:
        test_read_performance(date_str, enable_compression=True)

    print("\n=== 读取性能测试（关闭压缩） ===")
    for date_str, _, _ in test_cases:
        test_read_performance(date_str, enable_compression=False)

    print("\n=== 批量上传性能测试 ===")
    test_batch_upload("2025-04-16", "2025-04-18", stock_count=1000, factor_count=20, skip_weekends=True)

    print("\n=== 导出结果表格 ===")
    df_result = pd.DataFrame(results)
    df_result.to_csv("performance_results.csv", index=False)
    print("已保存结果至 performance_results.csv")

def plot_results():
    df = pd.read_csv("performance_results.csv")

    # Write performance plot
    df_write = df[df['type'] == 'write']
    plt.figure(figsize=(10, 5))
    plt.plot(df_write['stocks'], df_write['duration_sec'], marker='o')
    plt.title("Write Performance: Stock Count vs Duration")
    plt.xlabel("Number of Stocks")
    plt.ylabel("Time (seconds)")
    plt.grid(True)
    plt.savefig("plot_write_performance.png")
    print("Saved: plot_write_performance.png")

    # Read performance plot
    df_read_c = df[df['type'] == 'read_compressed']
    df_read_u = df[df['type'] == 'read_uncompressed']

    plt.figure(figsize=(10, 5))
    plt.plot(df_read_c['stocks'], df_read_c['duration_sec'], marker='o', label='Compressed')
    plt.plot(df_read_u['stocks'], df_read_u['duration_sec'], marker='s', label='Uncompressed')
    plt.title("Read Performance: Stock Count vs Duration (Compressed vs Uncompressed)")
    plt.xlabel("Number of Stocks")
    plt.ylabel("Time (seconds)")
    plt.legend()
    plt.grid(True)
    plt.savefig("plot_read_performance.png")
    print("Saved: plot_read_performance.png")

if __name__ == "__main__":
    run_all_tests()
    plot_results()