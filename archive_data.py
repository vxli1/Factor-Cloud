# archive_data.py

import requests
from datetime import datetime, timedelta
from config import CLICKHOUSE_URL, CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD

def archive_old_data(cutoff_days=300):
    cutoff_date = (datetime.now() - timedelta(days=cutoff_days)).strftime('%Y-%m-%d')
    print(f"开始归档 {cutoff_date} 前的数据...")

    # Step 1: 插入数据到归档表
    insert_sql = f"""
    INSERT INTO factor_data_archive
    SELECT * FROM factor_data
    WHERE timestamp < toDateTime('{cutoff_date}')
    """

    r_insert = requests.post(
        CLICKHOUSE_URL,
        data=insert_sql.encode("utf-8"),
        auth=(CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD),
        headers={"Content-Type": "text/plain"}
    )

    if r_insert.status_code == 200:
        print(f"插入归档表成功")
    else:
        print(f"插入失败：{r_insert.text}")
        return

    # Step 2: 删除主表中的老数据
    delete_sql = f"""
    ALTER TABLE factor_data DELETE
    WHERE timestamp < toDateTime('{cutoff_date}')
    """

    r_delete = requests.post(
        CLICKHOUSE_URL,
        data=delete_sql.encode("utf-8"),
        auth=(CLICKHOUSE_USERNAME, CLICKHOUSE_PASSWORD),
        headers={"Content-Type": "text/plain"}
    )

    if r_delete.status_code == 200:
        print(f"删除主表旧数据成功")
    else:
        print(f"删除失败：{r_delete.text}")

if __name__ == "__main__":
    archive_old_data()
