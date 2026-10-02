# Quick Reference: File Connections & Execution

## Module Dependency Map

```
┌─────────────────────────────────────────────────────────────┐
│                   AIRFLOW EXECUTION                         │
│            (scheduler picks up & runs tasks)                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         dags/stock_research_dag.py                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ def research_stock(ticker="AAPL"):                  │   │
│  │   Config.validate()                    ────────┐   │   │
│  │   researcher = StockResearcher()   ────────┐   │   │   │
│  │   storage = MarkdownStorage(...)   ────────┤   │   │   │
│  │   report = researcher.research(ticker) ──┐ │   │   │   │
│  │   file = storage.save(ticker, report) ──┐│ │   │   │   │
│  │   return str(file)                      ││ │   │   │   │
│  └─────────────────────────────────────────││─────────┘   │
│                                            ││ │            │
│                                            ││ │            │
│  Imports:                                  ││ │            │
│  - from stock_research.config import Config──┼┤            │
│  - from stock_research.research import ...  ├┤            │
│  - from stock_research.storage import ...  ───            │
└──────────────────────────────────────────────────────────────┘

                  │         │          │
                  ▼         ▼          ▼
    ┌──────────────────┐  ┌─────────────────────┐  ┌──────────────┐
    │  config.py       │  │ researcher.py       │  │  markdown.py │
    ├──────────────────┤  ├─────────────────────┤  ├──────────────┤
    │ - GEMINI_API_KEY │  │ StockResearcher:    │  │ MarkdownStor-│
    │ - GEMINI_MODEL   │  │ - research(ticker)  │  │ age:         │
    │ - OUTPUT_DIR     │  │ - Creates Gemini-   │  │ - save(t, c) │
    │ - TEMPERATURE    │  │   Client            │  │ - Creates    │
    │ - validate()     │  │ - Formats prompt    │  │   dirs       │
    │ - Reads from env │  │ - Calls API         │  │ - Writes md  │
    └────────┬─────────┘  └──────────┬──────────┘  └──────┬───────┘
             │                       │                    │
             │ Uses                  │ Uses               │ Uses
             │                       ▼                    │
             │            ┌──────────────────────┐       │
             │            │   client.py          │       │
             │            ├──────────────────────┤       │
             │            │ GeminiClient:        │       │
             │            │ - research(prompt)   │       │
             │            │ - Creates Google     │       │
             │            │   Search tool        │       │
             │            │ - Calls Gemini API   │       │
             │            │ - Returns text       │       │
             │            └──────────┬───────────┘       │
             │                       │                   │
             │ Provides API key      │ Uses prompt       │
             │                       ▼                   │
             │            ┌──────────────────────┐       │
             │            │   prompts.py         │       │
             │            ├──────────────────────┤       │
             │            │ STOCK_RESEARCH_-     │       │
             │            │   PROMPT template    │       │
             │            │ (20-point template)  │       │
             │            └──────────────────────┘       │
             │                                           │
             │                                           │ Writes to
             │                                           ▼
             │                      ┌─────────────────────────────┐
             └─────────────────────▶│ output/                     │
                                    │ ├─ AAPL/                    │
                                    │ │  ├─ 2024-01-15.md        │
                                    │ │  └─ 2024-01-20.md        │
                                    │ ├─ MSFT/                    │
                                    │ │  └─ 2024-01-15.md        │
                                    │ └─ ...                      │
                                    └─────────────────────────────┘
```

## Simple Execution Timeline

```
1. YOU: Click "Trigger DAG" in Airflow UI
   └─ Pass ticker="AAPL"

2. AIRFLOW: Creates a DAG Run
   └─ Schedules "research_stock" task

3. SCHEDULER: Picks up the task
   └─ Runs: research_stock(ticker="AAPL")

4. FUNCTION EXECUTION:
   
   ┌─ Config.validate()
   │  └─ Check: GEMINI_API_KEY exists ✓
   │
   ├─ researcher = StockResearcher()
   │  ├─ __init__ creates GeminiClient
   │  │  ├─ Read from Config: API_KEY, MODEL, TEMPERATURE
   │  │  └─ Initialize genai.Client() [but don't call API yet]
   │  └─ Store client reference
   │
   ├─ storage = MarkdownStorage(Config.OUTPUT_DIR)
   │  ├─ Receive: /path/to/output
   │  └─ Store directory path
   │
   ├─ report = researcher.research("AAPL")
   │  ├─ Get STOCK_RESEARCH_PROMPT from prompts.py
   │  ├─ Format template:
   │  │  "Prepare a comprehensive research report for AAPL"
   │  ├─ Call: client.research(formatted_prompt)
   │  │  ├─ Create Google Search tool
   │  │  ├─ Call Gemini API with Google Search enabled
   │  │  └─ [WAIT 2-5 minutes for API response with real-time web search]
   │  └─ Return: markdown text response
   │
   ├─ output_file = storage.save("AAPL", report)
   │  ├─ Create directory: /output/AAPL/
   │  ├─ Get date: 2024-01-15
   │  ├─ Create file path: /output/AAPL/2024-01-15.md
   │  ├─ Write content to file
   │  └─ Return: Path object
   │
   └─ return str(output_file)
      └─ Task complete! ✓

5. AIRFLOW: Task marked as SUCCESS
   ├─ Green checkmark in UI
   ├─ Log available for viewing
   └─ Return value stored (file path)

6. REPORT: Ready to use
   └─ File: output/AAPL/2024-01-15.md
      Contains: Full research report
```

## Where Each File Does What

| File | Location | Purpose | Called By | Calls |
|------|----------|---------|-----------|-------|
| `stock_research_dag.py` | `dags/` | DAG definition & task | Airflow | research_stock() |
| `config.py` | `src/` | Environment config | All modules | getenv() |
| `client.py` | `src/gemini/` | Gemini API wrapper | StockResearcher | genai.Client() |
| `prompts.py` | `src/research/` | Prompt template | StockResearcher | format() |
| `researcher.py` | `src/research/` | Research logic | research_stock() | GeminiClient |
| `markdown.py` | `src/storage/` | File storage | research_stock() | Path.write_text() |

## Function Call Chain

```
Airflow Scheduler
    │
    └─ Calls: research_stock(ticker="AAPL")
       │
       ├─ Calls: Config.validate()
       │  └─ Returns: None (or raises error)
       │
       ├─ Calls: StockResearcher()
       │  └─ Creates GeminiClient instance
       │
       ├─ Calls: MarkdownStorage(Config.OUTPUT_DIR)
       │  └─ Stores directory path
       │
       ├─ Calls: researcher.research("AAPL")
       │  │
       │  ├─ Reads: STOCK_RESEARCH_PROMPT from prompts.py
       │  │
       │  └─ Calls: client.research(formatted_prompt)
       │     │
       │     └─ Calls: self.client.models.generate_content()
       │        └─ Gemini API (external, takes 2-5 minutes)
       │           └─ Returns: Markdown report string
       │
       ├─ Calls: storage.save("AAPL", report)
       │  │
       │  └─ Calls: Path.write_text(report, encoding="utf-8")
       │     └─ Writes file to disk
       │
       └─ Returns: file_path string
          └─ Airflow logs and marks task as SUCCESS
```

## Data Transformations

```
INPUT: ticker = "AAPL"

Transform 1: Prompt Formatting
  STOCK_RESEARCH_PROMPT (template)
  + {ticker} = "AAPL"
  = "Prepare a comprehensive research report for AAPL..."

Transform 2: API Call
  Formatted Prompt
  + Gemini API (with Google Search)
  = Markdown Report Text
  
Transform 3: File Creation
  Ticker + Report Text + Current Date
  = File at: output/AAPL/2024-01-15.md

OUTPUT: File path and content on disk
```

## Configuration Flow

```
Environment Variables (.env file)
    ↓
    ├─ GEMINI_API_KEY
    ├─ GEMINI_MODEL
    ├─ OUTPUT_DIR
    └─ RESEARCH_TEMPERATURE
    
Config class reads these
    ↓
    ├─ GeminiClient reads: API_KEY, MODEL, TEMPERATURE
    ├─ MarkdownStorage reads: OUTPUT_DIR
    ├─ StockResearcher reads: indirectly through GeminiClient
    └─ research_stock() function reads: Config.validate()
```

## Error Points & Recovery

| Error | Where | Recovery |
|-------|-------|----------|
| Missing GEMINI_API_KEY | Config.validate() | Set env var and retry |
| Gemini returns empty | GeminiClient.research() | Raises RuntimeError, Airflow retries |
| Output dir missing | MarkdownStorage.save() | mkdir creates it automatically |
| Invalid ticker format | Prompt formatting | Converted to uppercase |
| API rate limit | Gemini API | Airflow waits, then retries |

## Running in Airflow

```bash
# 1. Place DAG in correct location
cp dags/stock_research_dag.py ~/airflow/dags/

# 2. Airflow scans and loads it
airflow dags list
# Output: stock_research in list

# 3. Trigger via UI or CLI
airflow dags trigger stock_research -c '{"ticker": "AAPL"}'

# 4. View execution
airflow dags list-runs -d stock_research

# 5. View logs
airflow tasks logs stock_research research_stock <RUN_DATE>

# 6. Check output file
cat output/AAPL/2024-01-15.md
```

## Key Takeaways

1. **DAG is the entry point**: Airflow only knows about `stock_research_dag.py`
2. **Function is the executor**: `research_stock()` orchestrates everything
3. **Modules are workers**: Each module has a single responsibility
4. **Config is shared**: All modules read from Config class
5. **Data flows one direction**: Input → Processing → Output → File
6. **Error handling is automatic**: Airflow handles retries and logging
7. **Extensibility**: Easy to add more tickers or change models

## Next Steps

To modify the system:

- **Add more tickers**: Loop in DAG definition
- **Change schedule**: Modify `schedule_interval`
- **Different model**: Change `GEMINI_MODEL` env var
- **Parallel execution**: Airflow runs multiple tasks automatically
- **Add more tasks**: Define more PythonOperators in DAG
