import requests
import pandas as pd
import ast
import re
import io
from config import CLICKHOUSE_URL, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD
from datetime import datetime, timedelta

def clean_and_parse_map(s):
    if not isinstance(s, str):
        return None
    try:
        s_clean = re.sub(r'(\w+):', r'"\1":', s)  # 把 f1:0.8 改成 "f1":0.8
        return ast.literal_eval(s_clean)
    except Exception:
        return None

def load_factor_data(date_str, clickhouse_url=CLICKHOUSE_URL, username=CLICKHOUSE_USERNAME, password=CLICKHOUSE_PASSWORD, enable_compression=True):
    """
    一键加载某天的训练用因子矩阵。
    包含SQL查询、active因子获取、Map解包、类型优化、future return计算
    """
    # Step 1: 查询数据
    query_data = f'''
    SELECT stock_ticker, core_factor1, core_factor2, dynamic_factors
    FROM factor_data
    WHERE timestamp = '{date_str}'
    FORMAT TabSeparatedWithNames
    '''

    headers = {'Content-Type': 'text/plain'}
    if enable_compression:
        headers['Accept-Encoding'] = 'gzip'

    res_data = requests.post(
        clickhouse_url,
        data=query_data.encode('utf-8'),
        auth=(username, password),
        headers=headers
    )

    df = pd.read_csv(io.StringIO(res_data.text), sep='\t')

    # Step 2: 获取活跃因子列表
    query_factors = """
    SELECT factor_name FROM factor_metadata WHERE status = 'active'
    FORMAT TabSeparatedWithNames
    """
    res_meta = requests.post(
        clickhouse_url,
        data=query_factors.encode('utf-8'),
        auth=(username, password),
        headers={'Content-Type': 'text/plain'}
    )
    df_meta = pd.read_csv(io.StringIO(res_meta.text), sep='\t')
    active_factors = df_meta['factor_name'].dropna().tolist()

    # Step 3: 解包 dynamic_factors 列为多列
    df['dynamic_factors'] = df['dynamic_factors'].apply(clean_and_parse_map)
    for f in active_factors:
        df[f] = df['dynamic_factors'].apply(lambda m: m.get(f) if isinstance(m, dict) else None)
    df.drop(columns=['dynamic_factors'], inplace=True)

    # Step 4: 类型压缩
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')

    # Step 5: 加载模拟价格表并计算 future return
    try:
        price_df = pd.read_csv("simulated_price_table.csv")
        price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
        current_date = pd.to_datetime(date_str)
        next_date = current_date + timedelta(days=1)

        today_price = price_df[price_df['timestamp'] == current_date][['stock_ticker', 'close_price']].set_index('stock_ticker')
        future_price = price_df[price_df['timestamp'] == next_date][['stock_ticker', 'close_price']].set_index('stock_ticker')

        return_df = pd.DataFrame(index=today_price.index)
        return_df['future_return'] = (future_price['close_price'] / today_price['close_price'] - 1)

        df = df.merge(return_df, how='left', left_on='stock_ticker', right_index=True)
    except Exception as e:
        print("[警告] 未能成功计算 future return, 原因:", str(e))

    return df

# 主运行函数
def main():
    df_ML_train = load_factor_data(date_str='2025-04-09')
    print(df_ML_train)

if __name__ == "__main__":
    main()