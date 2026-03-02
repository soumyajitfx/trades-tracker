import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend)

export default function DashboardPage({ metrics }) {
  const lineData = {
    labels: metrics.equity_curve?.map((p) => new Date(p.time).toLocaleDateString()) || [],
    datasets: [{ label: 'Equity Curve', data: metrics.equity_curve?.map((p) => p.equity) || [], borderColor: '#2dd4bf' }],
  }

  return (
    <>
      <section className="grid">
        <article className="card"><h3>Total Trades</h3><p>{metrics.total_trades}</p></article>
        <article className="card"><h3>Win Rate</h3><p>{metrics.win_rate}%</p></article>
        <article className="card"><h3>Total P/L</h3><p>${metrics.total_pnl}</p></article>
        <article className="card"><h3>Average R:R</h3><p>{metrics.avg_rr}</p></article>
      </section>
      <section className="card">
        <h3>Equity Curve</h3>
        <Line data={lineData} />
      </section>
      <section className="grid">
        <article className="card"><h3>Daily</h3>{Object.entries(metrics.breakdown?.daily || {}).map(([k, v]) => <p key={k}>{k}: {v.toFixed(2)}</p>)}</article>
        <article className="card"><h3>Weekly</h3>{Object.entries(metrics.breakdown?.weekly || {}).map(([k, v]) => <p key={k}>{k}: {v.toFixed(2)}</p>)}</article>
        <article className="card"><h3>Monthly</h3>{Object.entries(metrics.breakdown?.monthly || {}).map(([k, v]) => <p key={k}>{k}: {v.toFixed(2)}</p>)}</article>
      </section>
    </>
  )
}
