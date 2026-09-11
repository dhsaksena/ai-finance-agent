import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import './App.css'

const ENDPOINT = import.meta.env.VITE_API_ENDPOINT || 'http://localhost:8000/chat'

export default function App() {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') || 'dark'
    }
    return 'dark'
  })

  const [chats, setChats] = useState([])
  const [currentChatId, setCurrentChatId] = useState(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(t => t === 'dark' ? 'light' : 'dark')
  }

  const createChat = () => {
    const newChat = {
      id: Date.now(),
      title: 'New chat',
      messages: [],
      backendSessionId: null
    }
    setChats(prev => [newChat, ...prev])
    setCurrentChatId(newChat.id)
  }

  const selectChat = (chatId) => {
    setCurrentChatId(chatId)
  }

  const getCurrentChat = () => {
    return chats.find(c => c.id === currentChatId)
  }

  const updateChatTitle = (chatId, title) => {
    setChats(prev =>
      prev.map(chat =>
        chat.id === chatId ? { ...chat, title } : chat
      )
    )
  }

  const addMessage = (chatId, message) => {
    setChats(prev =>
      prev.map(chat =>
        chat.id === chatId
          ? { ...chat, messages: [...chat.messages, message] }
          : chat
      )
    )
  }

  const updateMessage = (chatId, messageIndex, updates) => {
    setChats(prev =>
      prev.map(chat => {
        if (chat.id === chatId) {
          const updatedChat = { ...chat }
          if ('backendSessionId' in updates) {
            updatedChat.backendSessionId = updates.backendSessionId
          }
          updatedChat.messages = chat.messages.map((msg, idx) =>
            idx === messageIndex ? { ...msg, ...updates } : msg
          )
          return updatedChat
        }
        return chat
      })
    )
  }

  return (
    <div className="app">
      <Sidebar
        chats={chats}
        currentChatId={currentChatId}
        onNewChat={createChat}
        onSelectChat={selectChat}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <ChatArea
        currentChat={getCurrentChat()}
        endpoint={ENDPOINT}
        onAddMessage={addMessage}
        onUpdateMessage={updateMessage}
        onUpdateChatTitle={updateChatTitle}
      />
    </div>
  )
}
