import { useState } from 'react'
import ConfidenceLedger from './ConfidenceLedger'

const speechSupported = typeof window !== 'undefined' && 'speechSynthesis' in window

export default function MessageBubble({ role, content, confidence, handover }) {
  const isUser = role === 'user'
  const [speaking, setSpeaking] = useState(false)

  function toggleSpeak() {
    if (!speechSupported) return
    if (speaking) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
      return
    }
    window.speechSynthesis.cancel() // stop any other message currently reading
    const utterance = new SpeechSynthesisUtterance(content)
    utterance.rate = 1.0
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    window.speechSynthesis.speak(utterance)
    setSpeaking(true)
  }

  return (
    <div className={`bubble-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="bubble">
        <div className="bubble-head">
          <span className="bubble-role">{isUser ? 'you' : 'ledgr'}</span>
          {!isUser && speechSupported && (
            <button
              type="button"
              className={`speak-button ${speaking ? 'speaking' : ''}`}
              onClick={toggleSpeak}
              aria-label={speaking ? 'Stop reading aloud' : 'Read aloud'}
              title={speaking ? 'Stop reading aloud' : 'Read aloud'}
            >
              {speaking ? (
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                  <rect x="2" y="2" width="9" height="9" rx="1.5" fill="currentColor" />
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M2 5.5V8.5H4.5L7.5 11V3L4.5 5.5H2Z" fill="currentColor" />
                  <path d="M9.5 4.5C10.3 5.3 10.3 8.7 9.5 9.5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" fill="none" />
                </svg>
              )}
            </button>
          )}
        </div>
        <p className="bubble-text">{content}</p>
        {!isUser && confidence !== undefined && (
          <ConfidenceLedger confidence={confidence} handover={handover} />
        )}
      </div>

      <style>{`
        .bubble-row {
          display: flex;
          margin-bottom: 18px;
        }
        .bubble-row.user {
          justify-content: flex-end;
        }
        .bubble-row.assistant {
          justify-content: flex-start;
        }
        .bubble {
          max-width: 72%;
          padding: 14px 16px;
          border-radius: var(--radius);
          border: 1px solid var(--border);
        }
        .bubble-row.user .bubble {
          background: var(--bg-elevated);
          border-color: var(--border-light);
        }
        .bubble-row.assistant .bubble {
          background: var(--bg-panel);
        }
        .bubble-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 6px;
        }
        .bubble-role {
          display: block;
          font-family: var(--font-mono);
          font-size: 10px;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--text-faint);
        }
        .speak-button {
          display: flex;
          align-items: center;
          justify-content: center;
          background: none;
          border: none;
          color: var(--text-faint);
          padding: 2px;
          transition: color 0.15s ease;
        }
        .speak-button:hover {
          color: var(--accent-gold);
        }
        .speak-button.speaking {
          color: var(--accent-rust);
        }
        .bubble-text {
          margin: 0;
          font-size: 14.5px;
          line-height: 1.55;
          color: var(--text);
          white-space: pre-wrap;
        }
      `}</style>
    </div>
  )
}