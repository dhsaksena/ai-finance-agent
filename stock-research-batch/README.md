# Stock Research Batch Processing

An Airflow-based batch processing system for generating comprehensive stock research reports using Google Gemini AI with real-time web search capabilities.

## Architecture

```
dags/
├── stock_research_dag.py          # Airflow DAG definition

src/stock_research/
├── config.py                      # Configuration management
├── gemini/
│   ├── __init__.py
│   └── client.py                  # Gemini API client wrapper
├── research/
│   ├── __init__.py
│   ├── prompts.py                 # Research prompt templates
│   └── researcher.py              # Research orchestration logic
└── storage/
    ├── __init__.py
    └── markdown.py                # Markdown file storage handler

output/                            # Generated research reports
```

## Components

### GeminiClient (gemini/client.py)
Wrapper around the Google Gemini API that:
- Initializes the Gemini client with your API key
- Configures Google Search as a grounding tool for real-time web data
- Calls the Gemini API with configurable temperature for consistency

### StockResearcher (research/researcher.py)
Orchestrates the research process:
- Takes a stock ticker symbol
- Formats the research prompt with the ticker
- Calls GeminiClient to generate the report
- Returns markdown-formatted content

### MarkdownStorage (storage/markdown.py)
Handles persistent storage:
- Creates ticker-specific directories
- Saves reports with date-stamped filenames
- Uses UTF-8 encoding for markdown content

### Config (config.py)
Centralized configuration:
- `GEMINI_MODEL`: Gemini model to use (default: gemini-3.8-flash)
- `GEMINI_API_KEY`: API key from environment variables
- `OUTPUT_DIR`: Directory for saving reports
- `RESEARCH_TEMPERATURE`: Model temperature for consistency (default: 0.2)

## Setup

### Prerequisites
- Python 3.8+
- Apache Airflow
- Google Gemini API credentials

### Installation

```bash
# Create virtual environment
python -m venv airflow_venv
source airflow_venv/bin/activate  # On Windows: airflow_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-api-key-here"
export OUTPUT_DIR="/path/to/output"  # Optional
```

### Environment Variables
- `GEMINI_API_KEY` (required): Your Google Gemini API key
- `GEMINI_MODEL` (optional): Model to use (default: gemini-3.8-flash)
- `OUTPUT_DIR` (optional): Output directory for reports
- `RESEARCH_TEMPERATURE` (optional): Model temperature (default: 0.2)

## Usage

### Running Airflow

```bash
# Initialize Airflow database
airflow db init

# Start the scheduler
airflow scheduler

# Start the web UI (in another terminal)
airflow webui
```

### Triggering the DAG

Via Airflow UI:
1. Navigate to the DAG list
2. Find "stock_research"
3. Click "Trigger DAG"

Via CLI:
```bash
airflow dags trigger stock_research -c '{"ticker": "AAPL"}'
```

### Running Standalone

```python
from stock_research.config import Config
from stock_research.research.researcher import StockResearcher
from stock_research.storage.markdown import MarkdownStorage

Config.validate()

researcher = StockResearcher()
storage = MarkdownStorage(Config.OUTPUT_DIR)

report = researcher.research("AAPL")
output_file = storage.save("AAPL", report)
print(f"Report saved to {output_file}")
```

## Report Contents

The generated research reports include:
- Company overview
- Stock price and market capitalization
- Quarterly/annual financial results
- Revenue and profit metrics
- EPS (Earnings Per Share)
- Free cash flow analysis
- Balance sheet overview
- Debt and cash position
- Earnings guidance
- Business segments
- Recent announcements
- Analyst expectations
- Growth drivers and risks
- Valuation metrics
- Insider activity and institutional ownership
- Upcoming events

All financial numbers include sources and clearly distinguish between reported and estimated figures.

## Output

Reports are saved as markdown files with the structure:
```
output/
├── AAPL/
│   ├── 2024-01-15.md
│   ├── 2024-01-20.md
│   └── ...
├── MSFT/
│   ├── 2024-01-15.md
│   └── ...
```

## Customization

### Adding Multiple Tickers

Modify the DAG to process multiple tickers:

```python
tickers = ["AAPL", "MSFT", "GOOGL"]

for ticker in tickers:
    PythonOperator(
        task_id=f"research_{ticker}",
        python_callable=research_stock,
        op_kwargs={"ticker": ticker},
        dag=dag,
    )
```

### Adjusting Temperature

Lower temperature (closer to 0) makes responses more deterministic. Adjust in `.env`:
```
RESEARCH_TEMPERATURE=0.1
```

### Using Different Model

Change the model in `.env`:
```
GEMINI_MODEL=gemini-3.8-flash
```

## Error Handling

- Configuration validation occurs before research starts
- Empty responses from Gemini raise `RuntimeError`
- Missing directories are created automatically
- API errors propagate with full traceback for debugging

## Performance

- Report generation typically takes 2-5 minutes depending on model and API load
- Airflow retries failed tasks once after 5 minutes
- No concurrency limits on ticker processing by default
