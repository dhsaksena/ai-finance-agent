# Deployment Guide

## Prerequisites

- Apache Airflow installed and configured
- Python 3.8 or higher
- Access to Google Gemini API with valid credentials
- Sufficient disk space for reports (varies by number of tickers)

## Step 1: Setup Environment

```bash
# Navigate to project directory
cd stock-research-batch

# Create and activate virtual environment
python -m venv airflow_venv
source airflow_venv/bin/activate  # On Windows: airflow_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

### Option A: Using .env file (already created)

The `.env` file should contain:
```
GEMINI_API_KEY=your-api-key-here
```

Make sure to add this directory to your Python path or set environment variables:

```bash
export GEMINI_API_KEY="your-api-key-here"
export OUTPUT_DIR="/path/to/output"
```

### Option B: Using Airflow Variables

In the Airflow UI or via CLI:
```bash
airflow variables set GEMINI_API_KEY "your-api-key-here"
airflow variables set OUTPUT_DIR "/path/to/output"
```

## Step 3: Initialize Airflow

```bash
# Set AIRFLOW_HOME if not already set
export AIRFLOW_HOME=~/airflow

# Initialize the database
airflow db init

# Create admin user (if needed)
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

## Step 4: Place DAG in Airflow

```bash
# Copy the DAG file to Airflow's DAG directory
cp dags/stock_research_dag.py ~/airflow/dags/

# Verify Airflow can find the DAG
airflow dags list
```

You should see `stock_research` in the list.

## Step 5: Start Airflow Services

```bash
# In terminal 1: Start the scheduler
airflow scheduler

# In terminal 2: Start the web server
airflow webui
```

The web UI will be available at `http://localhost:8080`

## Step 6: Configure DAG (Optional)

Edit `dags/stock_research_dag.py` to:

### Add Multiple Tickers

Replace the single task definition with:
```python
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]

for ticker in tickers:
    PythonOperator(
        task_id=f"research_{ticker}",
        python_callable=research_stock,
        op_kwargs={"ticker": ticker},
        dag=dag,
    )
```

### Enable Scheduling

Change the schedule from manual to periodic:
```python
dag = DAG(
    "stock_research",
    default_args=default_args,
    description="Research stocks using Gemini AI",
    schedule_interval="@weekly",  # Run weekly on Mondays
    catchup=False,
)
```

Valid schedule intervals:
- `"@once"`: Run once
- `"@hourly"`: Every hour
- `"@daily"`: Every day at midnight
- `"@weekly"`: Every Monday at midnight
- `"0 9 * * 1"`: Every Monday at 9 AM (cron format)

## Step 7: Trigger the DAG

### Via Web UI

1. Go to `http://localhost:8080`
2. Find `stock_research` in the DAG list
3. Click the "Trigger DAG" button
4. Optionally provide JSON configuration:
   ```json
   {"ticker": "AAPL"}
   ```

### Via CLI

```bash
# Trigger with default ticker (AAPL)
airflow dags trigger stock_research

# Trigger with specific ticker
airflow dags trigger stock_research -c '{"ticker": "MSFT"}'
```

### Via Python API

```python
from airflow.api.client.local_client import Client

client = Client(None, None)
client.trigger_dag("stock_research", conf={"ticker": "AAPL"})
```

## Step 8: Monitor Execution

### Via Web UI

1. Navigate to the DAG's detail page
2. Check task status in the "Tree View"
3. Click on a task to view logs
4. Monitor duration and success/failure status

### Via CLI

```bash
# View latest DAG runs
airflow dags list-runs -d stock_research

# View task logs
airflow tasks logs stock_research research_stock 2024-01-15T00:00:00+00:00
```

## Troubleshooting

### DAG Not Found

```bash
# Check DAG syntax
airflow dags list

# Check DAG parsing errors
airflow dags list-import-errors
```

### Missing GEMINI_API_KEY

Ensure environment variable is set in:
- Shell environment
- Airflow's `airflow_env` or `.env` file
- Or use Airflow Variables

Check with:
```bash
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"
```

### Output Directory Not Found

Create the output directory:
```bash
mkdir -p /path/to/output
chmod 755 /path/to/output
```

Or set `OUTPUT_DIR` environment variable to an existing directory.

### Gemini API Rate Limits

If you hit rate limits:
- Increase `retry_delay` in `default_args`
- Reduce concurrent DAG runs in Airflow config
- Add exponential backoff in `GeminiClient`

### Long Running Tasks

Gemini research can take 2-5 minutes per ticker:
- Monitor task duration in UI
- Consider running fewer tickers per schedule
- Enable task timeout to prevent hanging:

```python
default_args = {
    ...
    "execution_timeout": timedelta(minutes=10),
}
```

## Production Deployment

For production environments:

1. **Use managed scheduler**: Deploy Airflow using Astronomer, Cloud Composer, or MWAA
2. **Add monitoring**: Configure Airflow logs to send to ELK, Datadog, etc.
3. **Set up alerts**: Configure email/Slack notifications for task failures
4. **Use secrets backend**: Store API keys in a secrets manager (Vault, K8s Secrets, etc.)
5. **Enable HA**: Use PostgreSQL + multiple scheduler/worker instances
6. **Document runbook**: Create incident response guide for common failures
7. **Set up backups**: Backup metadata DB and output directory

## Verification

Test the setup:

```bash
# Run standalone test
python example_usage.py AAPL

# Check output
cat output/AAPL/*.md
```

If this works, Airflow deployment should also work.
