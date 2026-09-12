import './Sidebar.css'

export default function Sidebar({
  chats,
  currentChatId,
  onNewChat,
  onSelectChat,
  theme,
  onToggleTheme,
  useStreaming,
  onToggleStreaming
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          + New chat
        </button>
      </div>
      <div className="chat-list">
        {chats.map(chat => (
          <div
            key={chat.id}
            className={`chat-item ${chat.id === currentChatId ? 'active' : ''}`}
            onClick={() => onSelectChat(chat.id)}
            title={chat.title}
          >
            {chat.title}
          </div>
        ))}
      </div>
      <div className="sidebar-footer">
        <button
          className="streaming-toggle"
          onClick={onToggleStreaming}
          title={useStreaming ? 'Streaming enabled' : 'Streaming disabled'}
        >
          {useStreaming ? '⚡ Streaming' : '⏸ Non-streaming'}
        </button>
        <button className="theme-toggle" onClick={onToggleTheme}>
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>
    </div>
  )
}
