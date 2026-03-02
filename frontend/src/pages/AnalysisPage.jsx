export default function AnalysisPage({ metrics, trades, filters, setFilters, onSync }) {
  const change = (e) => setFilters((f) => ({ ...f, [e.target.name]: e.target.value }))

  const exportCsv = () => {
    const header = 'ticket,symbol,type,volume,open,close,profit\n'
    const rows = trades.map((t) => `${t.ticket},${t.symbol},${t.trade_type},${t.volume},${t.open_price},${t.close_price},${t.profit}`).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'trade-analysis.csv'
    a.click()
  }

  return (
    <>
      <section className="card">
        <h3>Filters</h3>
        <div className="filters">
          <input type="date" name="start" value={filters.start} onChange={change} />
          <input type="date" name="end" value={filters.end} onChange={change} />
          <input name="symbol" placeholder="Symbol" value={filters.symbol} onChange={change} />
          <select name="trade_type" value={filters.trade_type} onChange={change}>
            <option value="">All</option><option value="buy">Buy</option><option value="sell">Sell</option>
          </select>
          <button onClick={onSync}>Sync MT5</button>
          <button onClick={exportCsv}>Export CSV</button>
        </div>
      </section>
      <section className="grid">
        <article className="card"><h3>Max Drawdown</h3><p>{metrics.max_drawdown}</p></article>
        <article className="card"><h3>Sharpe Ratio</h3><p>{metrics.sharpe_ratio}</p></article>
      </section>
      <section className="card">
        <h3>Trade Table</h3>
        <table>
          <thead><tr><th>Ticket</th><th>Symbol</th><th>Type</th><th>P/L</th></tr></thead>
          <tbody>
            {trades.map((t) => <tr key={t.ticket}><td>{t.ticket}</td><td>{t.symbol}</td><td>{t.trade_type}</td><td>{t.profit}</td></tr>)}
          </tbody>
        </table>
      </section>
    </>
  )
}
