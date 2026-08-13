import { useState, useRef, useEffect } from 'react'
import MessageBubble from './components/MessageBubble'
import SessionPanel from './components/SessionPanel'
import InputBar from './components/InputBar'

const API_BASE = 'http://localhost:8000'
const SESSION_ID = 'dashboard-session-1'
const STORAGE_KEY = `ledgr-chat-${SESSION_ID}`

function loadPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { messages: [], facts: {}, sources: [] }
    return JSON.parse(raw)
  } catch {
    return { messages: [], facts: {}, sources: [] }
  }
}

export default function App() {
  const persisted = loadPersisted()
  const [messages, setMessages] = useState(persisted.messages)
  const [facts, setFacts] = useState(persisted.facts)
  const [sources, setSources] = useState(persisted.sources)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ messages, facts, sources }))
    } catch {
      // localStorage full or unavailable — chat still works, just won't persist across refresh
    }
  }, [messages, facts, sources])

  async function handleSend(text) {
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID, message: text }),
      })
      if (!res.ok) throw new Error(`Server responded ${res.status}`)
      const data = await res.json()

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply,
          confidence: data.confidence,
          handover: data.handover,
        },
      ])
      setFacts(data.remembered_facts || {})
      setSources(data.sources || [])
    } catch (err) {
      setError(
        `Couldn't reach the backend (${err.message}). Make sure uvicorn is running at ${API_BASE}.`
      )
    } finally {
      setLoading(false)
    }
  }

  function handleClear() {
    setMessages([])
    setFacts({})
    setSources([])
    setError(null)
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <svg className="brand-mark" width="30" height="30" viewBox="0 0 30 30" fill="none">
            <rect x="2" y="20" width="5" height="8" fill="var(--accent-gold-dim)" />
            <rect x="9" y="14" width="5" height="14" fill="var(--accent-gold)" />
            <rect x="16" y="7" width="5" height="21" fill="var(--accent-gold)" />
            <circle cx="21" cy="6" r="6.5" fill="var(--accent-gold)" />
            <text x="21" y="9.5" textAnchor="middle" fontSize="8" fontWeight="700" fill="var(--bg)" fontFamily="Inter, sans-serif">₹</text>
          </svg>
          <div className="brand-text">
            <span className="brand-eyebrow">AI Business Finance Advisor</span>
            <h1>Ledgr</h1>
          </div>
        </div>
        <span className="app-tagline">multi-agent · transparent · knows when to hand off</span>
        <button type="button" className="clear-button" onClick={handleClear} title="Clear conversation">
          Clear chat
        </button>
      </header>

      <div className="app-body">
        <main className="chat-column">
          <div className="chat-scroll" ref={scrollRef}>
            {messages.length === 0 && (
              <div className="empty-state">
                <p>Ledgr can help with cash flow, business loans, break-even analysis, GST, and working capital.</p>
                <p className="empty-hint">
                  For example: "What's my break-even point if fixed costs are 500000, price is 200, and cost per unit is 120?" or "How do I improve my DSO?"
                </p>
              </div>
            )}
            {messages.map((m, i) => (
              <MessageBubble key={i} {...m} />
            ))}
            {loading && (
              <div className="thinking">
                <span className="thinking-dot" />
                <span className="thinking-dot" />
                <span className="thinking-dot" />
              </div>
            )}
            {error && <p className="error-banner">{error}</p>}
          </div>
          <InputBar onSend={handleSend} disabled={loading} />
          <p className="disclaimer">
            Ledgr provides general business finance information, not personalized advice. For decisions specific to your business, consult an accountant or financial advisor.
          </p>
        </main>

        <SessionPanel facts={facts} sources={sources} />
      </div>

      <style>{`
        .app {
          height: 100vh;
          display: flex;
          flex-direction: column;
        }
        .app-header {
          padding: 16px 24px;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .brand-mark {
          flex-shrink: 0;
        }
        .brand-text {
          display: flex;
          flex-direction: column;
        }
        .brand-eyebrow {
          font-size: 10px;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--text-faint);
          font-family: var(--font-mono);
        }
        .app-header h1 {
          font-family: var(--font-display);
          font-size: 21px;
          font-weight: 600;
          margin: 0;
          color: var(--accent-gold);
          letter-spacing: 0.02em;
          line-height: 1.2;
        }
        .app-tagline {
          font-size: 12px;
          color: var(--text-faint);
          font-style: italic;
        }
        .clear-button {
          background: none;
          border: 1px solid var(--border-light);
          border-radius: var(--radius);
          color: var(--text-faint);
          font-size: 11.5px;
          padding: 6px 12px;
          font-family: var(--font-body);
          transition: color 0.15s ease, border-color 0.15s ease;
        }
        .clear-button:hover {
          color: var(--accent-rust);
          border-color: var(--accent-rust);
        }
        .disclaimer {
          font-size: 11px;
          color: var(--text-faint);
          text-align: center;
          padding: 0 24px 14px;
          margin: 0;
          line-height: 1.5;
        }
        .app-body {
          flex: 1;
          display: flex;
          overflow: hidden;
        }
        .chat-column {
          flex: 1;
          display: flex;
          flex-direction: column;
          min-width: 0;
        }
        .chat-scroll {
          flex: 1;
          overflow-y: auto;
          padding: 24px;
        }
        .empty-state {
          color: var(--text-muted);
          font-size: 14px;
          margin-top: 60px;
          text-align: center;
        }
        .empty-hint {
          color: var(--text-faint);
          font-size: 12.5px;
          font-style: italic;
          margin-top: 8px;
        }
        .thinking {
          display: flex;
          gap: 5px;
          padding: 14px 16px;
        }
        .thinking-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--accent-gold-dim);
          animation: pulse 1.2s ease-in-out infinite;
        }
        .thinking-dot:nth-child(2) { animation-delay: 0.15s; }
        .thinking-dot:nth-child(3) { animation-delay: 0.3s; }
        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }
        .error-banner {
          color: var(--accent-rust);
          font-size: 13px;
          background: var(--bg-elevated);
          border: 1px solid var(--accent-rust);
          border-radius: var(--radius);
          padding: 10px 14px;
        }
        @media (prefers-reduced-motion: reduce) {
          .thinking-dot { animation: none; }
        }
      `}</style>
    </div>
  )
}