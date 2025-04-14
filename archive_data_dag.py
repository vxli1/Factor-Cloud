# archive_data_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import sys

# 导入函数（确保路径正确）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from archive_data import archive_old_data

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'archive_old_clickhouse_data',
    default_args=default_args,
    description='定期归档 ClickHouse 老数据到归档表',
    schedule_interval='@daily',  # 每天跑一次
    start_date=datetime(2025, 4, 10),
    catchup=False,
)

archive_task = PythonOperator(
    task_id='archive_old_data_task',
    python_callable=archive_old_data,
    op_kwargs={'cutoff_days': 300},  # 自定义天数剥离冷热盘
    dag=dag
)

archive_task
