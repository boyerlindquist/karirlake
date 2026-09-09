from datetime import datetime, timedelta
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
local_tz = pendulum.timezone("Asia/Jakarta")

default_args = {
    'owner': 'data_engineer_sejati',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2024, 1, 1, tz=local_tz),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'job_market_lakehouse_pipeline',
    default_args=default_args,
    description='Pipeline harian narik loker Data, jadwal jam 6 Pagi',
    schedule_interval='0 6 * * *',
    catchup=False,
    max_active_runs=1,
) as dag:

    start_pipeline = EmptyOperator(
        task_id = 'start_pipeline'
    )

    scrape_kalibrr = BashOperator(
        task_id='scrape_kalibrr',
        bash_command='cd /opt/airflow && python scripts/scrapers/kalibrr.py'
    )
    
    scrape_glints = BashOperator(
        task_id='scrape_glints',
        bash_command='cd /opt/airflow && python scripts/scrapers/glints.py'
    )

    soda_check_bronze = BashOperator(
        task_id='soda_check_bronze',
        bash_command='cd /opt/airflow && soda scan -d lakehouse -c soda/configuration.yml soda/checks_bronze.yml'
    )

    dbt_run = BashOperator(
        task_id='dbt_build_lakehouse',
        bash_command='cd /opt/airflow && dbt clean --project-dir dbt_lakehouse --profiles-dir dbt_lakehouse && dbt run --project-dir dbt_lakehouse --profiles-dir dbt_lakehouse'
    )

    soda_check_gold = BashOperator(
        task_id='soda_check_gold',
        bash_command='cd /opt/airflow && soda scan -d lakehouse -c soda/configuration.yml soda/checks_gold.yml'
    )

    end_pipeline = EmptyOperator(
        task_id = 'end_pipeline'
    )

    start_pipeline >> [scrape_kalibrr, scrape_glints] >> soda_check_bronze >> dbt_run >> soda_check_gold >> end_pipeline
