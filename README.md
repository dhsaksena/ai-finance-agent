# AI Finance Agent

A command-line stock advisor built on the Anthropic Claude API. You ask it about a
stock in plain English; it confirms the ticker, pulls live fundamentals, optionally
reads your own saved research notes, and returns a **buy / hold / sell** judgment
grounded in the stock's own financials.

The agent runs a classic tool-use loop: Claude decides which tools to call, the code
executes them, and the results are fed back until Claude produces a final answer.

---

## How it works

```
You ─▶ main.py (chat loop)
          │
          ├─ loads your notes/*.md  ──▶ system prompt context
          │
          ▼
     Claude (claude-sonnet-5)  ◀── tool results ──┐
          │                                        │
          │ decides to call a tool                 │
          ▼                                        │
     search.py TOOLS ───────────────────────────────┘
       ├─ search_ticker(company_name)   → tickers.json (local lookup)
       ├─ get_stock_fundamentals(ticker)→ Yahoo Finance (yfinance)
       └─ get_company_research(ticker)  → research/<TICKER>.md
```

The system prompt (in `main.py`) enforces the workflow:

1. **Never guess a ticker** — always call `search_ticker` first; if not found, ask the user.
2. Call `get_stock_fundamentals` for the real numbers — the primary basis for the judgment.
3. Only if fundamentals leave a genuine gap in confidence, call `get_company_research`
   to read saved human notes *before* asking the user.
4. Judge on the stock's own merits only (valuation, profitability, growth, price trend) —
   portfolio fit and diversification are explicitly out of scope for now.

---

## Code layout

| File / dir | Purpose |
|---|---|
| `main.py` | Entry point. Runs the interactive chat loop, builds the system prompt from notes, calls the Claude API, and dispatches tool calls in `ask_advisor()`. |
| `search.py` | Defines the three tools and their `TOOLS` schema (the tool definitions sent to Claude): `search_ticker`, `get_stock_fundamentals` (uses `yfinance`), and `get_company_research`. |
| `ingest.py` | `load_notes()` — reads every `notes/*.md` file into memory so it can be injected into the system prompt. |
| `config.py` | Loads `.env` and defines base paths (`BASE_DIR`, `NOTES_DIR`, `RESEARCH_DIR`). |
| `tickers.json` | Local company-name → ticker-symbol map. The only source of truth for `search_ticker` (no internet lookup). |
| `notes/` | Your general investing preferences/rules (e.g. `watchlist.md`, `investing.md`). Loaded into **every** conversation as context. |
| `research/` | Per-company deep-research files named `<TICKER>.md` (e.g. `KIRLPNU.md`). Fetched on demand by `get_company_research`. |
| `requirements.txt` | Python dependencies. |
| `.env` | Your API keys — **not committed** (see `.env.example`). |
| `test.py` | Scratch/experimentation file (inspects the `claude_agent_sdk` API); not part of the app. |

### notes/ vs research/

- **`notes/`** = your global rules, always in context. Example thresholds from
  `watchlist.md`: cautious above P/E 30–35, prefer ROE > 15%, cautious above
  debt-to-equity 1.5–2.0, prefer revenue growth > 10% YoY.
- **`research/`** = per-ticker detail, pulled only when needed. File name must match
  the base ticker (exchange suffix stripped: `ZFCVINDIA.NS` → `research/ZFCVINDIA.md`).

---

## Setup

### Prerequisites
- Python 3.10+ (the code uses `list[dict[...]]` type hints)
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone and enter the project
```bash
git clone https://github.com/dhsaksena/ai-finance-agent.git
cd ai-finance-agent
```

### 2. Create a virtual environment and install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure your API key
Copy the example and fill in your key:
```bash
cp .env.example .env
```
Then edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=            # optional / reserved; not required to run the agent
```

### 4. Run

#### Option A: CLI Mode (Command Line)
```bash
python cli.py
```
You'll see:
```
Finance Agent ready. Ask a question (or 'exit' to quit).

You:
```

#### Option B: Server Mode (API for Frontend)
```bash
python server.py
```
The API will start on `http://localhost:8000` with:
- `POST /chat` - Submit a query and get agent response (maintains conversation history per session)
- `POST /sessions/{session_id}/clear` - Clear conversation history for a session
- `GET /health` - Health check endpoint

See the **UI Integration** section below for connecting the frontend.

---

## Usage

Ask about any company. Type `exit` or `quit` to stop.

```
You: Should I buy Kirloskar Pneumatic?
Advisor: ...buy/hold/sell judgment with reasoning from the fundamentals...
```

**To add a company** so the agent can find it:
1. Add its name → ticker to `tickers.json`.
2. (Optional) Add a `research/<TICKER>.md` file with deeper notes for the agent to read
   when the raw numbers aren't enough.

**To change the agent's global rules**, edit the files in `notes/` — they're loaded into
every conversation.

---

## UI Integration

The agent can be connected to a web UI for chat interactions. The frontend at `personal-assistant-ui/` is configured to communicate with the server.

### Setup for Full Stack

1. **Terminal 1**: Start the backend server
   ```bash
   cd /path/to/claude-sdk-finance-agent
   source .venv/bin/activate
   python server.py
   ```
   Server runs on `http://localhost:8000`

2. **Terminal 2**: Start the frontend development server
   ```bash
   cd /path/to/personal-assistant-ui
   npm install          # First time only
   npm run dev
   ```
   UI opens on `http://localhost:5173`

3. **Open your browser** to `http://localhost:5173` and start chatting!

### How it works
- Each chat session in the UI gets a unique `session_id`
- The UI sends queries to the backend's `/chat` endpoint
- The backend maintains conversation history per session
- Agent responses include full context from previous messages in the same session

---

## Notes & limitations

- `search_ticker` does a simple substring match against `tickers.json` — it does not
  hit the internet, so unknown companies must be added manually.
- Fundamentals come from Yahoo Finance via `yfinance`; some fields may be missing for a
  given company and are treated as "unknown," not zero.
- The model is set to `claude-sonnet-5` in `cli.py`.
- `TAVILY_API_KEY` is present in the environment scaffolding but not currently used by
  the running agent.
- Session history is stored in-memory on the server; restarting the server clears all
  conversation histories.
