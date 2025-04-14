import requests
import random
from datetime import datetime

url = 'https://wej3jcde4a.ap-northeast-1.aws.clickhouse.cloud:8443/?database=default'
username = 'default'
password = 'g3_28R1E7IFJG'

today = datetime(2025, 4, 9).strftime('%Y-%m-%d %H:%M:%S')
stock_list = ['000001', '000002', '000003']
factor_names = ['f1', 'f2', 'f3']

rows = []
for stock in stock_list:
    dynamic_map = {f: round(random.uniform(-1, 1), 4) for f in factor_names}
    map_items = ", ".join([f"'{k}', {v}" for k, v in dynamic_map.items()])
    row = f"('{today}', '{stock}', {round(random.random(),4)}, {round(random.random(),4)}, map({map_items}))"
    rows.append(row)

insert_sql = f"""
INSERT INTO factor_data (timestamp, stock_ticker, core_factor1, core_factor2, dynamic_factors)
VALUES {','.join(rows)}
"""

response = requests.post(
    url,
    data=insert_sql.encode('utf-8'),
    auth=(username, password),
    headers={'Content-Type': 'text/plain'}
)

print("sucessfully uploaded" if response.status_code == 200 else f"failed: {response.text}")
