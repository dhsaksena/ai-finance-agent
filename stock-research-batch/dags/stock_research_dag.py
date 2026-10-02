import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stock_research.config import Config
from stock_research.research.researcher import StockResearcher
from stock_research.storage.markdown import MarkdownStorage


def get_stocks_to_research():
    """Load stocks from tickers.json."""
    tickers_file = Path(__file__).parent.parent.parent / "claude-sdk-finance-agent" / "tickers.json"
    with open(tickers_file) as f:
        tickers_dict = json.load(f)
        tickers = list(tickers_dict.values())
        return [{"ticker": t} for t in tickers]


def research_stock(ticker: str):
    """Research a stock and save the report."""
    Config.validate()

    researcher = StockResearcher()
    storage = MarkdownStorage(Config.OUTPUT_DIR)

    print(f"Starting research for {ticker}...")
    report = researcher.research(ticker)

    output_file = storage.save(ticker, report)
    print(f"Research written to {output_file}")

    return {"ticker": ticker, "output_file": str(output_file)}


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2024, 1, 1),
}

dag = DAG(
    "stock_research",
    default_args=default_args,
    description="Research multiple stocks using Gemini AI with dynamic task mapping",
    schedule=None,
    catchup=False,
)

load_stocks_task = PythonOperator(
    task_id="load_stocks",
    python_callable=get_stocks_to_research,
    dag=dag,
)

research_tasks = PythonOperator.partial(
    task_id="research_stock",
    python_callable=research_stock,
    dag=dag,
).expand(op_kwargs=load_stocks_task.output)

load_stocks_task >> research_tasks
