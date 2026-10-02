# System Architecture & Execution Flow

## File Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AIRFLOW WEBUI/CLI                            │
│           (You trigger the DAG from browser or CLI)             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Triggers
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 stock_research_dag.py (DAG)                     │
│                     (dags/ folder)                              │
│                                                                 │
│  - Defines the DAG "stock_research"                            │
│  - Defines the PythonOperator task "research_stock"           │
│  - Calls research_stock() function with ticker                │
│  - Imports: Config, StockResearcher, MarkdownStorage          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Calls research_stock(ticker="AAPL")
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│            research_stock() Function (in DAG file)              │
│                                                                 │
│  1. Validates Config                                           │
│  2. Creates StockResearcher instance                           │
│  3. Creates MarkdownStorage instance                           │
│  4. Calls researcher.research(ticker)                          │
│  5. Calls storage.save(ticker, report)                         │
│  6. Returns file path                                          │
└────┬──────────────────────────────────────────────────┬─────────┘
     │                                                  │
     │ Creates                                         │ Calls
     ▼                                                 ▼
┌──────────────────────────┐  ┌─────────────────────────────────┐
│   Config (config.py)     │  │  StockResearcher (research/)    │
│  (src/ folder)           │  │                                 │
│                          │  │  - Initializes GeminiClient     │
│ - GEMINI_API_KEY         │  │  - Calls client.research(prompt)│
│ - GEMINI_MODEL           │  │  - Passes ticker to format      │
│ - OUTPUT_DIR             │  │    the research prompt          │
│ - RESEARCH_TEMPERATURE   │  │  - Returns markdown report      │
│ - validate()             │  │                                 │
└──────────────────────────┘  └────────────┬────────────────────┘
                                           │
                                           │ Calls client.research()
                                           ▼
                              ┌─────────────────────────────────┐
                              │  GeminiClient (gemini/)         │
                              │                                 │
                              │ - Initializes Google Gemini API │
                              │ - Sets up Google Search tool    │
                              │ - Calls API with prompt         │
                              │ - Returns text response         │
                              │                                 │
                              │ Uses: STOCK_RESEARCH_PROMPT     │
                              └────────────┬────────────────────┘
                                           │
                                           │ Formats prompt with
                                           │ ticker symbol
                                           ▼
                              ┌─────────────────────────────────┐
                              │  prompts.py (research/)         │
                              │                                 │
                              │  STOCK_RESEARCH_PROMPT          │
                              │  - Template string              │
                              │  - Research instructions        │
                              │  - Output format (Markdown)     │
                              │  - Data sources (20+ points)    │
                              └─────────────────────────────────┘

     ┌────────────────────────────────────────────────┐
     │ Back to research_stock() function              │
     │ After report generated from Gemini             │
     └────────────────────────────────────────────────┘
                           │
                           │ Calls storage.save()
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│         MarkdownStorage (storage/markdown.py)                   │
│                                                                 │
│ - Creates ticker directory: output/AAPL/                       │
│ - Gets current date                                            │
│ - Creates filename: YYYY-MM-DD.md                              │
│ - Writes report to file                                        │
│ - Returns file path                                            │
└────────────────┬──────────────────────────────────────────────┘
                 │
                 │ Writes to disk
                 ▼
        ┌───────────────────────┐
        │   output/AAPL/        │
        │   2024-01-15.md       │
        │   2024-01-20.md       │
        │   ...                 │
        └───────────────────────┘
```

## File Structure & Relationships

```
stock-research-batch/
├── dags/
│   └── stock_research_dag.py         ← Entry point (Airflow picks this up)
│       ├── Imports Config from config.py
│       ├── Imports StockResearcher from researcher.py
│       ├── Imports MarkdownStorage from markdown.py
│       └── Defines DAG and tasks
│
├── src/stock_research/
│   ├── __init__.py                    ← Makes it a Python package
│   │
│   ├── config.py                      ← Configuration management
│   │   ├── Reads environment variables
│   │   ├── Provides GEMINI_API_KEY, OUTPUT_DIR, etc.
│   │   └── Used by: GeminiClient, DAG function
│   │
│   ├── gemini/
│   │   ├── __init__.py
│   │   └── client.py                  ← Gemini API wrapper
│   │       ├── Initializes Google Gemini client
│   │       ├── Uses Config for API key and model
│   │       ├── Calls Gemini API with Google Search
│   │       └── Returns markdown text response
│   │
│   ├── research/
│   │   ├── __init__.py
│   │   ├── prompts.py                 ← Research prompt template
│   │   │   └── STOCK_RESEARCH_PROMPT (template with {ticker})
│   │   │
│   │   └── researcher.py              ← Research orchestrator
│   │       ├── Initializes GeminiClient
│   │       ├── Formats prompt with ticker
│   │       ├── Calls client.research()
│   │       └── Returns markdown report
│   │
│   └── storage/
│       ├── __init__.py
│       └── markdown.py                ← File storage handler
│           ├── Takes base directory from Config
│           ├── Creates ticker directories
│           ├── Saves reports with date stamps
│           └── Returns file path
│
├── output/                             ← Where reports are saved
│   ├── AAPL/
│   │   └── 2024-01-15.md
│   ├── MSFT/
│   │   └── 2024-01-15.md
│   └── ...
│
├── .env                                ← Environment variables
│   └── GEMINI_API_KEY=...
│
├── requirements.txt                    ← Python dependencies
│   ├── apache-airflow
│   ├── google-genai
│   └── python-dotenv
│
└── README.md / DEPLOYMENT.md           ← Documentation
```

## Execution Flow - Step by Step

### Phase 1: Setup (When Airflow starts)

```
1. Airflow scans dags/ folder
   ↓
2. Loads stock_research_dag.py
   ↓
3. Parses DAG definition
   ├─ Creates DAG object "stock_research"
   ├─ Creates PythonOperator task "research_stock"
   └─ Task is now registered in Airflow
   ↓
4. DAG appears in Airflow UI
```

### Phase 2: Trigger (When you click "Trigger DAG")

```
1. User triggers DAG from Airflow UI/CLI
   Example: airflow dags trigger stock_research -c '{"ticker": "AAPL"}'
   ↓
2. Airflow creates a new DAG Run
   ├─ DAG Run ID: stock_research__2024-01-15T10:30:00+00:00
   └─ Passes config: {"ticker": "AAPL"}
   ↓
3. Airflow queues the "research_stock" task
```

### Phase 3: Task Execution (When scheduler picks up the task)

```
1. Airflow Scheduler picks up research_stock task
   ↓
2. Executor starts task execution
   ↓
3. Python interpreter runs research_stock() function
   │
   ├─ Step A: Config.validate()
   │  └─ Checks if GEMINI_API_KEY is set
   │
   ├─ Step B: researcher = StockResearcher()
   │  ├─ Creates StockResearcher instance
   │  └─ StockResearcher.__init__() creates GeminiClient
   │     └─ GeminiClient reads Config for API key & model
   │
   ├─ Step C: storage = MarkdownStorage(Config.OUTPUT_DIR)
   │  └─ Creates storage handler with output directory
   │
   ├─ Step D: report = researcher.research("AAPL")
   │  ├─ StockResearcher.research("AAPL")
   │  ├─ Formats STOCK_RESEARCH_PROMPT with ticker="AAPL"
   │  ├─ Calls GeminiClient.research(formatted_prompt)
   │  ├─ GeminiClient creates Google Search tool
   │  ├─ Calls Gemini API with prompt
   │  │  └─ Gemini searches web for AAPL info in real-time
   │  └─ Returns markdown report string
   │
   ├─ Step E: output_file = storage.save("AAPL", report)
   │  ├─ MarkdownStorage.save("AAPL", report)
   │  ├─ Creates directory: output/AAPL/
   │  ├─ Gets current date: 2024-01-15
   │  ├─ Creates file: output/AAPL/2024-01-15.md
   │  ├─ Writes report content to file
   │  └─ Returns Path object
   │
   └─ Step F: return str(output_file)
      └─ Task returns success with file path
```

### Phase 4: Task Completion

```
1. Task execution finishes
   ├─ Success state set in DB
   ├─ Task log saved
   └─ Return value stored (optional)
   ↓
2. Airflow UI shows task as green/success
   ├─ You can view logs
   ├─ You can see execution duration
   └─ Output file is at: output/AAPL/2024-01-15.md
   ↓
3. DAG Run completes
   └─ All tasks done
```

## Data Flow Example: From Trigger to Report

```
INPUT:
  ticker = "AAPL"
  date = 2024-01-15
  
TRANSFORMATION FLOW:
  
  "AAPL" 
    ↓
    │ researcher.research("AAPL")
    │
  STOCK_RESEARCH_PROMPT template
    + ticker="AAPL"
    = "You are an equity research analyst. Prepare a comprehensive 
       research report for AAPL. Use Google Search to retrieve..."
    ↓
    │ GeminiClient.research(prompt)
    │
  [Gemini API Call with Google Search]
    + Real-time web search
    + Temperature = 0.2 (deterministic)
    = "# AAPL Research Report\n\n## Company Overview\n..."
    ↓
    │ MarkdownStorage.save("AAPL", report)
    │
  Directory: output/AAPL/
  Filename: 2024-01-15.md
  Content: [Full markdown report]
  
OUTPUT:
  File: /path/to/output/AAPL/2024-01-15.md
  Contains: Comprehensive stock research report in markdown
```

## Key Concepts

### 1. DAG (Directed Acyclic Graph)
- **What**: A workflow definition in Airflow
- **File**: `stock_research_dag.py`
- **Contains**: Task definitions and their dependencies
- **In this case**: Single task that research stocks

### 2. Task
- **What**: A unit of work in the DAG
- **Type**: PythonOperator (runs Python function)
- **Function**: `research_stock(ticker)`
- **Execution**: Sequential, triggered by scheduler

### 3. Operator
- **Type**: PythonOperator
- **Purpose**: Wraps Python function for Airflow execution
- **Parameters**: `python_callable`, `op_kwargs`, `task_id`

### 4. Config Management
- **Purpose**: Centralized configuration
- **Source**: Environment variables
- **Usage**: Shared across all modules
- **Pattern**: GeminiClient, StockResearcher, MarkdownStorage all use Config

### 5. Dependency Injection
- **Pattern**: Modules accept dependencies in constructor
- **Example**: 
  ```python
  researcher = StockResearcher()  # Auto-creates GeminiClient
  storage = MarkdownStorage(Config.OUTPUT_DIR)  # Receives config
  ```

## Class Initialization Chain

```
When research_stock() is called:

1. StockResearcher() is instantiated
   ├─ __init__ calls GeminiClient()
   │  ├─ Reads Config.GEMINI_MODEL
   │  ├─ Reads Config.RESEARCH_TEMPERATURE
   │  └─ Creates genai.Client() with API key from Config.GEMINI_API_KEY
   └─ Stores client reference

2. MarkdownStorage(Config.OUTPUT_DIR) is instantiated
   ├─ Receives output directory path
   └─ Stores for later use

3. researcher.research("AAPL") is called
   ├─ Gets prompt template from prompts.py
   ├─ Formats with ticker: "AAPL"
   └─ Calls self.client.research(formatted_prompt)
      └─ GeminiClient sends to API with Google Search enabled

4. storage.save("AAPL", report) is called
   ├─ Creates output/AAPL/ directory
   ├─ Gets current date
   └─ Writes file to disk
```

## Error Handling Flow

```
If GEMINI_API_KEY is not set:
  Config.validate() 
    └─ Raises ValueError
       └─ Task fails with error
       └─ Airflow retries (configured as 1 retry after 5 mins)
       └─ If still fails, shows in UI as red/failed

If Gemini returns empty response:
  GeminiClient.research()
    └─ if not response.text:
       └─ Raises RuntimeError("Gemini returned empty response")
       └─ Task fails with traceback visible in logs

If output directory doesn't exist:
  MarkdownStorage.save()
    └─ mkdir(parents=True, exist_ok=True)
    └─ Creates directory automatically (no error)
```

## Scheduling Example

### Manual Trigger (No Schedule)
```python
schedule_interval=None  # Default
# Must manually trigger via UI or CLI
```

### Daily Schedule
```python
schedule_interval="@daily"
# Runs every day at midnight UTC
```

### Cron Schedule
```python
schedule_interval="0 9 * * 1"  # Every Monday at 9 AM
# Can run for multiple tickers automatically
```

### Multiple Tickers Example
```python
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    PythonOperator(
        task_id=f"research_{ticker}",
        python_callable=research_stock,
        op_kwargs={"ticker": ticker},
        dag=dag,
    )
# Creates 3 parallel tasks in the DAG
# Each runs independently
```

## Summary

**The complete flow:**

```
Airflow Webui/CLI
    ↓ Trigger
DAG Definition (stock_research_dag.py)
    ↓ Runs
research_stock() Function
    ├─ Creates instances (Config, StockResearcher, MarkdownStorage)
    ├─ research_stock → StockResearcher → GeminiClient → Gemini API
    ├─ Gemini searches web with Google Search
    ├─ Returns markdown report
    └─ MarkdownStorage saves to file
Disk Output (output/AAPL/2024-01-15.md)
```

Every file is connected through Python imports and dependency injection. The DAG is the orchestrator, the function is the executor, and the modules are the workers.
