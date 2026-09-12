import { useState, useEffect, useRef } from 'react'
import MessageList from './MessageList'
import ChatForm from './ChatForm'
import './ChatArea.css'

export default function ChatArea({
  currentChat,
  endpoint,
  useStreaming,
  onAddMessage,
  onUpdateMessage,
  onUpdateChatTitle
}) {
  const [isLoading, setIsLoading] = useState(false)
  const messageListRef = useRef(null)

  const handleStreamingMessage = async (query, chatId, sessionId) => {
    const userMessage = { role: 'user', text: query }
    onAddMessage(chatId, userMessage)

    if (currentChat.messages.length === 0) {
      const title = query.length > 30 ? query.slice(0, 30) + '…' : query
      onUpdateChatTitle(chatId, title)
    }

    const pendingMessageIndex = currentChat.messages.length + 1
    const pendingMessage = { role: 'agent', text: '', status: 'streaming', chunks: [] }
    onAddMessage(chatId, pendingMessage)

    try {
      const payload = { query }
      if (sessionId) {
        payload.session_id = sessionId
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) throw new Error(`Server returned ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullText = ''
      let toolsUsed = []
      let backendSessionId = sessionId

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines[lines.length - 1]

        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i]
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))

              if (event.type === 'text') {
                fullText += event.content
                onUpdateMessage(chatId, pendingMessageIndex, {
                  text: fullText,
                  chunks: [...(pendingMessage.chunks || []), event.content]
                })
              } else if (event.type === 'tool_call') {
                toolsUsed.push(event.tool_name)
                onUpdateMessage(chatId, pendingMessageIndex, {
                  text: fullText,
                  toolsUsed
                })
              } else if (event.type === 'end') {
                onUpdateMessage(chatId, pendingMessageIndex, {
                  text: fullText,
                  status: 'success',
                  toolsUsed,
                  backendSessionId
                })
              } else if (event.type === 'error') {
                onUpdateMessage(chatId, pendingMessageIndex, {
                  text: fullText || `Error: ${event.message}`,
                  status: 'error'
                })
              }
            } catch (e) {
              console.error('Failed to parse event:', line, e)
            }
          }
        }
      }
    } catch (err) {
      const msg = `Error: ${err.message}`
      onUpdateMessage(chatId, pendingMessageIndex, {
        text: msg,
        status: 'error'
      })
      throw err
    }
  }

  const handleSendMessage = async (query) => {
    if (!currentChat) return

    const chatId = currentChat.id
    setIsLoading(true)

    try {
      if (useStreaming) {
        await handleStreamingMessage(query, chatId, currentChat.backendSessionId)
      } else {
        const userMessage = { role: 'user', text: query }
        onAddMessage(chatId, userMessage)

        if (currentChat.messages.length === 0) {
          const title = query.length > 30 ? query.slice(0, 30) + '…' : query
          onUpdateChatTitle(chatId, title)
        }

        const pendingMessageIndex = currentChat.messages.length + 1
        const pendingMessage = { role: 'agent', text: 'Thinking…', status: 'pending' }
        onAddMessage(chatId, pendingMessage)

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
      }
    } catch (err) {
      if (!useStreaming) {
        const msg = `Error: ${err.message}`
        const pendingMessageIndex = currentChat.messages.length - 1
        onUpdateMessage(chatId, pendingMessageIndex, {
          text: msg,
          status: 'error'
        })
      }
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
