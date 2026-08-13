const TICKS = 20

function tierFor(confidence) {
  if (confidence >= 0.7) return { color: 'var(--accent-sage)', label: 'high confidence' }
  if (confidence >= 0.45) return { color: 'var(--accent-gold)', label: 'moderate confidence' }
  return { color: 'var(--accent-rust)', label: 'low confidence' }
}

export default function ConfidenceLedger({ confidence, handover }) {
  const filled = Math.round(confidence * TICKS)
  const tier = handover
    ? { color: 'var(--accent-rust)', label: 'handed to a human' }
    : tierFor(confidence)

  return (
    <div className="ledger" role="img" aria-label={`Confidence: ${Math.round(confidence * 100)} percent, ${tier.label}`}>
      <div className="ledger-ticks">
        {Array.from({ length: TICKS }).map((_, i) => (
          <span
            key={i}
            className="ledger-tick"
            style={{
              background: i < filled ? tier.color : 'var(--border-light)',
              opacity: i < filled ? 1 : 0.5,
            }}
          />
        ))}
      </div>
      <span className="ledger-score" style={{ color: tier.color }}>
        {Math.round(confidence * 100)}%
      </span>
      <span className="ledger-label">{tier.label}</span>

      <style>{`
        .ledger {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 8px;
        }
        .ledger-ticks {
          display: flex;
          gap: 2px;
          align-items: flex-end;
        }
        .ledger-tick {
          width: 3px;
          height: 14px;
          border-radius: 1px;
          transition: background 0.3s ease;
        }
        .ledger-score {
          font-family: var(--font-mono);
          font-size: 13px;
          font-weight: 500;
          min-width: 38px;
        }
        .ledger-label {
          font-family: var(--font-body);
          font-size: 12px;
          color: var(--text-faint);
          font-style: italic;
        }
      `}</style>
    </div>
  )
}
