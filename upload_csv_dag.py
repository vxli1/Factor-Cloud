from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import os
import sys

# 确保可以导入 upload_data.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upload_data import upload_dataframe

# DAG 默认参数
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 定义 DAG
dag = DAG(
    'upload_csv_to_clickhouse',
    default_args=default_args,
    description='每日上传 CSV 到 ClickHouse',
    schedule_interval='@daily',
    start_date=datetime(2025, 4, 10),
    catchup=False
)

def read_and_upload_csv(**context):
    date_str = context['ds']  # Airflow 注入的 dag 执行日期，格式为 'YYYY-MM-DD'
    file_path = f'/opt/airflow/data/factors_{date_str}.csv'
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    df = pd.read_csv(file_path, converters={'dynamic_factors': eval})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    upload_dataframe(df)

upload_task = PythonOperator(
    task_id='upload_daily_csv',
    python_callable=read_and_upload_csv,
    provide_context=True,
    dag=dag
)
