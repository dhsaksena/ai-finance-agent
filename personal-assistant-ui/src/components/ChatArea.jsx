import { useState, useEffect, useRef } from 'react'
import MessageList from './MessageList'
import ChatForm from './ChatForm'
import './ChatArea.css'

export default function ChatArea({
  currentChat,
  endpoint,
  onAddMessage,
  onUpdateMessage,
  onUpdateChatTitle
}) {
  const [isLoading, setIsLoading] = useState(false)
  const messageListRef = useRef(null)

  const handleSendMessage = async (query) => {
    if (!currentChat) return

    const chatId = currentChat.id
    const userMessage = { role: 'user', text: query }
    onAddMessage(chatId, userMessage)

    if (currentChat.messages.length === 0) {
      const title = query.length > 30 ? query.slice(0, 30) + '…' : query
      onUpdateChatTitle(chatId, title)
    }

    setIsLoading(true)
    const pendingMessageIndex = currentChat.messages.length + 1

    const pendingMessage = { role: 'agent', text: 'Thinking…', status: 'pending' }
    onAddMessage(chatId, pendingMessage)

    try {
      const payload = { query }
      if (currentChat.backendSessionId) {
        payload.session_id = currentChat.backendSessionId
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) throw new Error(`Server returned ${res.status}`)

      const data = await res.json()
      const answer = data.response ?? '(empty response)'

      onUpdateMessage(chatId, pendingMessageIndex, {
        text: answer,
        status: 'success',
        backendSessionId: data.session_id
      })
    } catch (err) {
      const msg = `Error: ${err.message}`
      onUpdateMessage(chatId, pendingMessageIndex, {
        text: msg,
        status: 'error'
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-area">
      <header className="chat-header">Finance Agent</header>
      <MessageList
        ref={messageListRef}
        messages={currentChat?.messages || []}
      />
      <ChatForm
        onSend={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  )
}
