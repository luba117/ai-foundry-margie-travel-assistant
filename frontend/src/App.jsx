import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  text: "Welcome to **Margie's Travel**! ✈️ I'm your AI-powered travel assistant.\n\nAsk me about destinations, hotel packages, tourist attractions, or anything travel-related. I have access to our full brochure collection and real-time travel information!",
  time: formatTime(new Date()),
}

// ---------------------------------------------------------------------------
// TypingIndicator
// ---------------------------------------------------------------------------
function TypingIndicator() {
  return (
    <div className="message assistant">
      <div className="avatar assistant-avatar">✈️</div>
      <div className="bubble assistant-bubble typing-bubble">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Message
// ---------------------------------------------------------------------------
function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && <div className="avatar assistant-avatar">✈️</div>}

      <div className={`bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
        {isUser ? (
          <p className="message-text">{msg.text}</p>
        ) : (
          <div className="message-text markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
          </div>
        )}
        <span className="message-time">{msg.time}</span>
      </div>

      {isUser && <div className="avatar user-avatar">👤</div>}
    </div>
  )
}

// ---------------------------------------------------------------------------
// SuggestedPrompts
// ---------------------------------------------------------------------------
const SUGGESTED_PROMPTS = [
  '🗼 Tell me about Paris packages',
  '🏙️ What can I do in Tokyo?',
  '🏖️ Best Dubai hotel packages',
  '🎭 London travel recommendations',
]

function SuggestedPrompts({ onSelect }) {
  return (
    <div className="suggested-prompts">
      <p className="suggested-label">Try asking:</p>
      <div className="prompt-chips">
        {SUGGESTED_PROMPTS.map((p) => (
          <button key={p} className="chip" onClick={() => onSelect(p)}>
            {p}
          </button>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
export default function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [error, setError] = useState('')

  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  // Auto-scroll to the latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
  }, [input])

  const sendMessage = useCallback(
    async (text) => {
      const userText = (text ?? input).trim()
      if (!userText || isLoading) return

      setError('')
      setInput('')
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: 'user', text: userText, time: formatTime(new Date()) },
      ])
      setIsLoading(true)

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userText, session_id: sessionId }),
        })

        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail ?? `HTTP ${res.status}`)
        }

        const data = await res.json()
        setSessionId(data.session_id)
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'assistant',
            text: data.reply,
            time: formatTime(new Date()),
          },
        ])
      } catch (err) {
        setError(`Something went wrong: ${err.message}`)
      } finally {
        setIsLoading(false)
        textareaRef.current?.focus()
      }
    },
    [input, isLoading, sessionId],
  )

  const clearChat = useCallback(async () => {
    if (sessionId) {
      await fetch(`/api/chat/${sessionId}`, { method: 'DELETE' }).catch(() => {})
    }
    setSessionId('')
    setError('')
    setMessages([{ ...WELCOME_MESSAGE, time: formatTime(new Date()) }])
  }, [sessionId])

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
      }
    },
    [sendMessage],
  )

  const showSuggestions = messages.length === 1 && !isLoading

  return (
    <div className="app-shell">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <span className="header-icon">✈️</span>
          <div>
            <h1 className="header-title">Margie's Travel Assistant</h1>
            <p className="header-subtitle">AI-powered travel recommendations</p>
          </div>
        </div>
        <button className="new-chat-btn" onClick={clearChat} title="Start a new conversation">
          + New Chat
        </button>
      </header>

      {/* Chat window */}
      <main className="chat-window">
        <div className="messages-container">
          {messages.map((msg) => (
            <Message key={msg.id} msg={msg} />
          ))}

          {isLoading && <TypingIndicator />}

          {error && (
            <div className="error-banner">
              ⚠️ {error}
              <button className="error-dismiss" onClick={() => setError('')}>
                ✕
              </button>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {showSuggestions && <SuggestedPrompts onSelect={(p) => sendMessage(p)} />}
      </main>

      {/* Input bar */}
      <footer className="input-bar">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="message-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about destinations, hotels, activities… (Enter to send)"
            rows={1}
            disabled={isLoading}
          />
          <button
            className={`send-btn ${isLoading || !input.trim() ? 'disabled' : ''}`}
            onClick={() => sendMessage()}
            disabled={isLoading || !input.trim()}
            title="Send message"
          >
            {isLoading ? '⏳' : '➤'}
          </button>
        </div>
        <p className="input-hint">Shift + Enter for new line</p>
      </footer>
    </div>
  )
}
