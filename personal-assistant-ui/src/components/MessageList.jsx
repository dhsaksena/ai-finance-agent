import { useEffect, useRef } from 'react'
import Message from './Message'
import './MessageList.css'

export default function MessageList({ messages }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      setTimeout(() => {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight
      }, 0)
    }
  }, [messages])

  return (
    <div className="message-list" ref={scrollRef}>
      {messages.length === 0 ? (
        <div className="empty-state">Ask something to start.</div>
      ) : (
        messages.map((msg, idx) => (
          <Message key={idx} message={msg} />
        ))
      )}
    </div>
  )
}
