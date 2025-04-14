## 1. 启动Airflow环境
mkdir airflow_project
cd airflow_project

curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml'
mkdir -p dags logs plugins
echo -e "AIRFLOW_UID=$(id -u)" > .env

## 2. 初始化Airflow
docker compose up airflow-init

## 3. 启动全部服务
docker compose up # 或者 docker compose up -d（在后台运行，不影响跑其他代码）

## 4. 访问Airflow UI: http://localhost:8080, 默认设置可后续修改 username: airflow, password: airflow

## 5. 
docker compose down