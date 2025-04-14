# Factor-Cloud (ClickHouse + Python)

This system enables scalable storage, training, and dynamic management of alpha factors for quantitative strategies. It supports dynamic factor addition/removal, ML training, cold-hot data separation, and metadata versioning.

---

## 🔁 Overall Logic Flow

```mermaid
graph LR
A[Collect raw factor data] --> B[upload_dataframe.py to ClickHouse]
B --> C[Update factor_metadata table (active/deprecated)]
C --> D[load_factor_data.py constructs factor matrix]
D --> E[Train ML model]
E --> F[Upload trained factor values]
F --> G[Update metadata status (promoted/deprecated)]
G --> H[archive_data.py separates cold/hot data]
H --> D
```

---

## 🗂️ Tables in ClickHouse

### 1. `factor_data`
```sql
CREATE TABLE factor_data (
  timestamp DateTime,
  stock_ticker String,
  core_factor1 Float64,
  core_factor2 Float64,
  dynamic_factors Map(String, Float64)
) ENGINE = MergeTree()
PARTITION BY toDate(timestamp)
ORDER BY (stock_ticker, timestamp);
```

### 2. `factor_metadata`
```sql
CREATE TABLE factor_metadata (
  factor_name String,
  status Enum('active', 'deprecated', 'promoted'),
  created_time DateTime,
  deprecated_time DateTime
) ENGINE = MergeTree()
ORDER BY factor_name;
```

---

## 🧠 ML Training (Simulation)

```python
from xgboost import XGBRegressor
model = XGBRegressor()
model.fit(X_train, y_train)
important_factors = X_train.columns[model.feature_importances_ > 0.01].tolist()
```

- You can then upload these factors as new predictions and tag them in metadata as `promoted`.

---

## 🔄 Deciding Core vs Dynamic Factors

| Criteria                            | Promote to Core | Stay Dynamic  |
|-------------------------------------|------------------|----------------|
| Used in >80% of training iterations | ✅               | ❌             |
| Frequently appear in top features   | ✅               | ❌             |
| Recently added or under testing     | ❌               | ✅             |
| Volatile or unstable performance    | ❌               | ✅             |

You may write a script to update `factor_metadata` accordingly and reflect changes in your `upload_dataframe.py`.

---

## 🧊 Cold-Hot Data Separation

Run `archive_data.py` regularly (e.g., via Airflow):
- Move data older than T days to `factor_data_archive`
- Keep hot table fast and lightweight

---

## ✅ Future Work
- Add `train_and_promote.py` to automate: training, alpha selection, metadata updates
- Build a materialized view for top core factors
- Log training performance of each factor

---

Maintainer: *Jinyang Li*
Version: 2025.04
