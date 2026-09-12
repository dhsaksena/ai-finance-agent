import './Message.css'

export default function Message({ message }) {
  const isUser = message.role === 'user'
  const classes = ['message-row', isUser ? 'user' : 'agent']

  let bubbleClasses = ['bubble']
  if (message.status === 'pending') {
    bubbleClasses.push('pending')
  } else if (message.status === 'streaming') {
    bubbleClasses.push('streaming')
  } else if (message.status === 'error') {
    bubbleClasses.push('error')
  }

  return (
    <div className={classes.join(' ')}>
      <div className={bubbleClasses.join(' ')}>
        {message.text}
        {message.status === 'streaming' && <span className="streaming-cursor">▌</span>}
        {message.toolsUsed && message.toolsUsed.length > 0 && (
          <div className="tools-used">
            Tools: {message.toolsUsed.join(', ')}
          </div>
        )}
      </div>
    </div>
  )
}
