import { useState, useRef, useEffect } from 'react'

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

export default function InputBar({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef(null)
  const voiceSupported = Boolean(SpeechRecognition)

  useEffect(() => {
    if (!voiceSupported) return
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'en-IN'

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setValue((prev) => (prev ? `${prev} ${transcript}` : transcript))
    }
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)

    recognitionRef.current = recognition
    return () => recognition.abort()
  }, [voiceSupported])

  function toggleListening() {
    if (!voiceSupported || disabled) return
    if (listening) {
      recognitionRef.current.stop()
      setListening(false)
    } else {
      recognitionRef.current.start()
      setListening(true)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      {voiceSupported && (
        <button
          type="button"
          className={`mic-button ${listening ? 'listening' : ''}`}
          onClick={toggleListening}
          disabled={disabled}
          aria-label={listening ? 'Stop recording' : 'Start voice input'}
          title={listening ? 'Stop recording' : 'Ask by voice'}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="6" y="1.5" width="6" height="9" rx="3" fill="currentColor" />
            <path d="M3 8.5C3 11.5 5.5 13.5 9 13.5C12.5 13.5 15 11.5 15 8.5" stroke="currentColor" strokeWidth="1.3" fill="none" />
            <path d="M9 13.5V16.5" stroke="currentColor" strokeWidth="1.3" />
          </svg>
        </button>
      )}
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={listening ? 'Listening…' : 'Ask Ledgr about cash flow, loans, break-even, GST, or working capital…'}
        disabled={disabled}
        autoFocus
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        Send
      </button>

      <style>{`
        .input-bar {
          display: flex;
          gap: 10px;
          padding: 16px 24px;
          border-top: 1px solid var(--border);
          background: var(--bg);
        }
        .input-bar input {
          flex: 1;
          background: var(--bg-input);
          border: 1px solid var(--border-light);
          border-radius: var(--radius);
          padding: 12px 14px;
          color: var(--text);
          font-family: var(--font-body);
          font-size: 14.5px;
        }
        .input-bar input::placeholder {
          color: var(--text-faint);
        }
        .input-bar input:focus {
          border-color: var(--accent-gold-dim);
        }
        .input-bar button[type="submit"] {
          background: var(--accent-gold);
          color: var(--bg);
          border: none;
          border-radius: var(--radius);
          padding: 0 22px;
          font-weight: 600;
          font-size: 14px;
          letter-spacing: 0.01em;
          transition: background 0.15s ease;
        }
        .input-bar button[type="submit"]:hover:not(:disabled) {
          background: #d4ae66;
        }
        .input-bar button[type="submit"]:disabled {
          background: var(--border-light);
          color: var(--text-faint);
          cursor: not-allowed;
        }
        .mic-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 44px;
          flex-shrink: 0;
          background: var(--bg-input);
          border: 1px solid var(--border-light);
          border-radius: var(--radius);
          color: var(--text-faint);
          transition: color 0.15s ease, border-color 0.15s ease;
        }
        .mic-button:hover:not(:disabled) {
          color: var(--accent-gold);
          border-color: var(--accent-gold-dim);
        }
        .mic-button.listening {
          color: var(--accent-rust);
          border-color: var(--accent-rust);
          animation: mic-pulse 1.2s ease-in-out infinite;
        }
        .mic-button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        @keyframes mic-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @media (prefers-reduced-motion: reduce) {
          .mic-button.listening { animation: none; }
        }
      `}</style>
    </form>
  )
}