# Finance Agent UI

A modern React-based chat interface for interacting with a Finance Agent. Built with Vite for fast development and optimized performance.

## Features

- 💬 Real-time chat interface with message history
- ⚡ Streaming support for real-time text generation with Server-Sent Events (SSE)
- 🎨 Light/Dark theme support with persistent preference
- 📱 Responsive design
- ⚙️ Toggleable streaming mode for flexible API interaction
- 🔌 Configurable API endpoint for Finance Agent backend
- 🛠️ Tool usage tracking and display

## Getting Started

### Prerequisites

- Node.js 14+ and npm/yarn

### Installation

```bash
# Install dependencies
npm install

# Create .env file (optional, uses default localhost endpoint)
cp .env.example .env
```

### Development

```bash
# Start the dev server (runs on http://localhost:5173)
npm run dev
```

The app will hot-reload as you make changes.

### Building for Production

```bash
# Build the app
npm run build

# Preview the production build
npm run preview
```

## Configuration

### API Endpoint

The Finance Agent API base endpoint can be configured via environment variable:

```env
VITE_API_ENDPOINT=http://localhost:8000
```

If not provided, defaults to `http://localhost:8000`.

The app uses two endpoints:
- **Non-streaming**: `{VITE_API_ENDPOINT}/chat` - Returns complete response
- **Streaming**: `{VITE_API_ENDPOINT}/chat/stream` - Returns Server-Sent Events stream

### Streaming Mode

By default, the UI uses **streaming mode** for real-time text generation. You can toggle between streaming and non-streaming modes using the button in the sidebar (⚡ Streaming / ⏸ Non-streaming). The preference is automatically saved in browser storage.

### Running with the Finance Agent Backend

1. **Start the backend server** (in another terminal):
   ```bash
   cd ../claude-sdk-finance-agent
   source .venv/bin/activate
   python server.py
   ```
   The server will start on `http://localhost:8000`

2. **Start the frontend dev server**:
   ```bash
   npm run dev
   ```
   The UI will open on `http://localhost:5173`

3. **Begin chatting!** Each conversation maintains full context across multiple messages in the same session.

### Backend API Contract

#### Non-Streaming Endpoint (`/chat`)

POST request format:
```json
{
  "query": "user question here",
  "session_id": "optional-uuid-for-maintaining-context"
}
```

Response format:
```json
{
  "response": "agent response here",
  "session_id": "uuid-for-maintaining-context-across-messages"
}
```

#### Streaming Endpoint (`/chat/stream`)

POST request format (same as above):
```json
{
  "query": "user question here",
  "session_id": "optional-uuid-for-maintaining-context"
}
```

Response format: Server-Sent Events (SSE) stream with events:
```
data: {"type": "text", "content": "text chunk..."}\n\n
data: {"type": "tool_call", "tool_name": "function_name", "tool_use_id": "id"}\n\n
data: {"type": "tool_results_submitted"}\n\n
data: {"type": "end", "stop_reason": "end_turn"}\n\n
data: {"type": "error", "message": "error message"}\n\n
```

The `session_id` is automatically managed by the UI to maintain conversation history for each chat session.

## Project Structure

```
src/
├── components/
│   ├── Sidebar.jsx          # Chat history sidebar
│   ├── ChatArea.jsx         # Main chat container
│   ├── MessageList.jsx      # Message display area
│   ├── Message.jsx          # Individual message bubble
│   └── ChatForm.jsx         # Input form
├── App.jsx                  # Main app component
├── index.css                # Global styles & theme variables
└── main.jsx                 # Entry point
```

## Customization

### Theme Colors

Edit the CSS variables in `src/index.css` to customize the appearance:

```css
:root[data-theme="dark"] {
  --bg: #0B0B0D;
  --accent: #4F8CFF;
  /* ... more variables */
}
```

### Component Styling

Each component has its own CSS file for easy maintenance and customization.

## License

MIT
