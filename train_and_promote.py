import pandas as pd
import requests
from xgboost import XGBRegressor
from config import CLICKHOUSE_URL, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD
from load_factor_data import load_factor_data
from upload_data import upload_dataframe
from datetime import datetime, timedelta
import io
import os


HISTORY_DIR = "importance_history"
COOLDOWN_DAYS = 90


def train_and_promote(date_str='2025-04-10', importance_threshold=0.01):
    print(f"[步骤 1] 加载 {date_str} 的因子矩阵数据...")
    df = load_factor_data(date_str)

    if 'future_return' not in df.columns:
        raise ValueError("训练数据中必须包含 'future_return' 列。")

    y = df['future_return']
    X = df.drop(columns=['stock_ticker', 'future_return'])

    for col in X.columns:
        if X[col].dtype == 'object':
            try:
                X[col] = X[col].astype('float32')
            except:
                print(f"[警告] 因子 {col} 无法转换为数值，将被删除")
                X.drop(columns=[col], inplace=True)

    print("[步骤 2] 使用带标签数据训练 XGBoost 模型...")
    model = XGBRegressor(n_estimators=100, max_depth=4)
    model.fit(X, y)

    importance = model.feature_importances_
    selected_factors = X.columns[importance > importance_threshold].tolist()

    print(f"[步骤 3] 更新因子历史表现，并标记冷却期超过 {COOLDOWN_DAYS} 天的因子为 deprecated")

    os.makedirs(HISTORY_DIR, exist_ok=True)
    hist_path = os.path.join(HISTORY_DIR, "factor_daily_importance.csv")
    today = pd.to_datetime(date_str)
    today_str = today.strftime("%Y-%m-%d")

    importance_df = pd.DataFrame({
        'factor_name': X.columns,
        'importance': importance,
        'date': today_str
    })

    if os.path.exists(hist_path):
        hist_df = pd.read_csv(hist_path)
        full_df = pd.concat([hist_df, importance_df], ignore_index=True)
    else:
        full_df = importance_df

    full_df.to_csv(hist_path, index=False)

    since_date = (today - timedelta(days=COOLDOWN_DAYS)).strftime("%Y-%m-%d")
    recent_df = full_df[full_df['date'] >= since_date]

    summary = recent_df.groupby('factor_name')['importance'].apply(
        lambda x: (x <= importance_threshold).all()
    )

    to_deprecate = summary[summary].index.tolist()

    for factor in to_deprecate:
        sql = f"""
        ALTER TABLE factor_metadata UPDATE status = 'deprecated'
        WHERE factor_name = '{factor}' AND status = 'active'
        """
        res = requests.post(
            CLICKHOUSE_URL,
            data=sql.encode('utf-8'),
            auth=(CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD),
            headers={'Content-Type': 'text/plain'}
        )
        if res.status_code == 200:
            print(f"标记因子为 deprecated: {factor}")
        else:
            print(f"标记因子 {factor} 失败: {res.text}")

    df['predicted_alpha'] = model.predict(X)
    print("[步骤 4] 模型预测完成，部分结果预览：")
    print(df[['stock_ticker', 'predicted_alpha']].head())

    df[['stock_ticker', 'predicted_alpha']].to_csv(f"predicted_alpha_{date_str}.csv", index=False)
    print(f"已保存预测 alpha 因子得分到 predicted_alpha_{date_str}.csv")

    importance_df = pd.DataFrame({
        'factor_name': X.columns,
        'importance': importance
    })
    importance_df['type'] = importance_df['factor_name'].apply(
        lambda x: 'core' if x.startswith('core_') else 'dynamic'
    )
    importance_df = importance_df.sort_values(by='importance', ascending=False)
    importance_df.to_csv(f"factor_importance_rank_{date_str}.csv", index=False)
    print("[步骤 5] 因子重要性评分已保存为 factor_importance_rank_{}.csv".format(date_str))

    high_score_factors = importance_df[importance_df['importance'] > importance_threshold]['factor_name'].tolist()
    factor_columns = ['stock_ticker'] + high_score_factors
    df_result = df[factor_columns].copy()

    dynamic_cols = [f for f in high_score_factors if not f.startswith('core_')]
    if len(dynamic_cols) > 0:
        dynamic_part = df_result[dynamic_cols].copy()
        df_result['dynamic_factors'] = dynamic_part.apply(lambda row: {k: float(row[k]) for k in row.index}, axis=1)
    else:
        df_result['dynamic_factors'] = [{} for _ in range(len(df_result))]

    final_df = pd.DataFrame({
        'timestamp': pd.to_datetime(date_str),
        'stock_ticker': df_result['stock_ticker'],
        'core_factor1': df['core_factor1'] if 'core_factor1' in df else 0.0,
        'core_factor2': df['core_factor2'] if 'core_factor2' in df else 0.0,
        'dynamic_factors': df_result['dynamic_factors']
    })

    final_df.to_csv(f"refactored_factor_table_{date_str}.csv", index=False)
    print("[步骤 6] 已构造符合主因子表结构的 DataFrame，并保存为 refactored_factor_table_{}.csv".format(date_str))

    print("[步骤 7] 正在上传因子结果至 ClickHouse...")
    upload_dataframe(final_df, overwrite=True)
    print("上传完成")

    return selected_factors


if __name__ == "__main__":
    train_and_promote(date_str='2025-04-10')