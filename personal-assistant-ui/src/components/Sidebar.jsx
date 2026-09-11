import './Sidebar.css'

export default function Sidebar({
  chats,
  currentChatId,
  onNewChat,
  onSelectChat,
  theme,
  onToggleTheme
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
      <button className="theme-toggle" onClick={onToggleTheme}>
        Switch to {theme === 'dark' ? 'light' : 'dark'}
      </button>
    </div>
  )
}
