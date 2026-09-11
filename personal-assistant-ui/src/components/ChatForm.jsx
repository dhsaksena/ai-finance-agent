import { useState } from 'react'
import './ChatForm.css'

export default function ChatForm({ onSend, isLoading }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed || isLoading) return

    onSend(trimmed)
    setQuery('')
  }

  return (
    <form className="chat-form" onSubmit={handleSubmit}>
      <div className="input-wrap">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask something…"
          disabled={isLoading}
          autoComplete="off"
          autoFocus
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
        >
          Send
        </button>
      </div>
    </form>
  )
}
