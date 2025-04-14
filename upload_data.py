# upload_dataframe.py

import requests
import pandas as pd
import io
from config import CLICKHOUSE_URL, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD
from datetime import datetime, timedelta

def insert_metadata_if_missing(factor_names):
    query = """
    SELECT factor_name FROM factor_metadata FORMAT TabSeparatedWithNames
    """
    res = requests.post(
        CLICKHOUSE_URL,
        data=query.encode('utf-8'),
        auth=(CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD),
        headers={'Content-Type': 'text/plain'}
    )
    existing = []
    if res.status_code == 200:
        df = pd.read_csv(io.StringIO(res.text), sep='\t')
        existing = df['factor_name'].tolist()

    new_factors = [f for f in factor_names if f not in existing]
    if new_factors:
        rows = [
            f"('{f}', 'active', now(), toDateTime('1970-01-01 00:00:00'))"
            for f in new_factors
        ]
        insert_sql = f"""
        INSERT INTO factor_metadata (factor_name, status, created_time, deprecated_time)
        VALUES {','.join(rows)}
        """
        res = requests.post(
            CLICKHOUSE_URL,
            data=insert_sql.encode('utf-8'),
            auth=(CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD),
            headers={'Content-Type': 'text/plain'}
        )
        if res.status_code == 200:
            print(f"已插入 {len(new_factors)} 个因子元数据")
        else:
            print(f"插入因子元数据失败: {res.text}")

def upload_dataframe(df, overwrite=True):
    if df.empty:
        print("DataFrame is empty. Nothing to upload.")
        return

    date_str = df['timestamp'].iloc[0].strftime('%Y-%m-%d')

    all_factors = set()
    for d in df['dynamic_factors']:
        all_factors.update(d.keys())
    insert_metadata_if_missing(list(all_factors))

    if overwrite:
        delete_sql = f"""
        ALTER TABLE factor_data DELETE WHERE toDate(timestamp) = toDate('{date_str}')
        """
        del_res = requests.post(
            CLICKHOUSE_URL,
            data=delete_sql.encode('utf-8'),
            auth=(CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD),
            headers={'Content-Type': 'text/plain'}
        )
        if del_res.status_code == 200:
            print(f"已清除 {date_str} 的旧数据")

    rows = []
    for _, row in df.iterrows():
        map_items = ", ".join([f"'{k}', {v}" for k, v in row['dynamic_factors'].items()])
        row_sql = f"("
        row_sql += f"'{row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}', "
        row_sql += f"'{row['stock_ticker']}', {row['core_factor1']}, {row['core_factor2']}, map({map_items})"
        row_sql += ")"
        rows.append(row_sql)

    insert_sql = f"""
    INSERT INTO factor_data (timestamp, stock_ticker, core_factor1, core_factor2, dynamic_factors)
    VALUES {','.join(rows)}
    """

    res = requests.post(
        CLICKHOUSE_URL,
        data=insert_sql.encode('utf-8'),
        auth=(CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD),
        headers={'Content-Type': 'text/plain'}
    )

    if res.status_code == 200:
        print(f"上传成功，共 {len(df)} 行")
    else:
        print(f"上传失败: {res.text}")

def upload_batch_dataframe(start_date, end_date=None, stock_list=None, factor_names=None, overwrite=False, skip_weekends=False, specific_dates=None):
    from generate_data import generate_mock_data

    if specific_dates:
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in specific_dates]
    else:
        if end_date is None:
            end_date = start_date
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        dates = [start_dt + timedelta(days=i) for i in range((end_dt - start_dt).days + 1)]

    for date in dates:
        if skip_weekends and date.weekday() >= 5:
            continue
        date_str = date.strftime("%Y-%m-%d")
        df = generate_mock_data(date_str, stock_list, factor_names)
        upload_dataframe(df, overwrite=overwrite)

if __name__ == "__main__":
    from generate_data import generate_mock_data
    df = generate_mock_data("2025-04-10") # 替换为真实数据
    upload_dataframe(df)

    upload_batch_dataframe(
        start_date='2025-04-05',
        end_date='2025-04-10',
        stock_list=['000001', '000002'], # 替换为真实数据
        factor_names=['f1', 'f2', 'f3'],
        overwrite=True,
        skip_weekends=True
    )