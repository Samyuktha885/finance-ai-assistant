const FACT_LABELS = {
  monthly_revenue: 'Monthly revenue',
  employee_count: 'Employees',
  industry: 'Industry',
}

export default function SessionPanel({ facts, sources }) {
  const factEntries = Object.entries(facts || {})

  return (
    <aside className="panel">
      <section className="panel-section">
        <h2 className="panel-heading">Session ledger</h2>
        <p className="panel-sub">what Ledgr remembers about your business</p>
        {factEntries.length === 0 ? (
          <p className="panel-empty">Nothing recorded yet — mention your revenue, team size, or industry.</p>
        ) : (
          <dl className="fact-list">
            {factEntries.map(([key, value]) => (
              <div className="fact-row" key={key}>
                <dt>{FACT_LABELS[key] || key}</dt>
                <dd>{String(value)}</dd>
              </div>
            ))}
          </dl>
        )}
      </section>

      <div className="panel-divider" />

      <section className="panel-section">
        <h2 className="panel-heading">Sources</h2>
        <p className="panel-sub">what the last reply drew from</p>
        {(!sources || sources.length === 0) ? (
          <p className="panel-empty">No knowledge-base sources used for the last reply.</p>
        ) : (
          <ul className="source-list">
            {sources.map((s, i) => (
              <li className="source-item" key={i}>
                <div className="source-head">
                  <span className="source-doc">{s.doc_id}</span>
                  <span className="source-score">{Math.round(s.score * 100)}%</span>
                </div>
                <p className="source-snippet">{s.snippet}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <style>{`
        .panel {
          width: 300px;
          flex-shrink: 0;
          background: var(--bg-panel);
          border-left: 1px solid var(--border);
          padding: 24px 20px;
          overflow-y: auto;
        }
        .panel-section {
          margin-bottom: 8px;
        }
        .panel-heading {
          font-family: var(--font-display);
          font-size: 15px;
          font-weight: 600;
          margin: 0 0 2px 0;
          color: var(--text);
        }
        .panel-sub {
          font-size: 11.5px;
          color: var(--text-faint);
          margin: 0 0 14px 0;
          font-style: italic;
        }
        .panel-empty {
          font-size: 12.5px;
          color: var(--text-faint);
          line-height: 1.5;
        }
        .panel-divider {
          height: 1px;
          background: var(--border);
          margin: 22px 0;
        }
        .fact-list {
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .fact-row {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          border-bottom: 1px dotted var(--border-light);
          padding-bottom: 6px;
        }
        .fact-row dt {
          font-size: 12.5px;
          color: var(--text-muted);
        }
        .fact-row dd {
          margin: 0;
          font-family: var(--font-mono);
          font-size: 13px;
          color: var(--accent-gold);
        }
        .source-list {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .source-item {
          background: var(--bg-elevated);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 10px 12px;
        }
        .source-head {
          display: flex;
          justify-content: space-between;
          margin-bottom: 6px;
        }
        .source-doc {
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--accent-teal);
        }
        .source-score {
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--text-faint);
        }
        .source-snippet {
          margin: 0;
          font-size: 12px;
          line-height: 1.5;
          color: var(--text-muted);
        }
      `}</style>
    </aside>
  )
}
