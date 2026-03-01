import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'

export default function ProfitSummary({ data }) {
  if (!data) return (
    <div className="card green-accent">
      <div className="section-title">Resumo Econômico</div>
      <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
        <div style={{ fontSize: '28px' }}>💰</div>
        <span style={{ fontSize: '13px', color: 'var(--text-dim)' }}>Execute uma simulação</span>
      </div>
    </div>
  )

  const log = data.log || []
  const totalRevEnergy = log.reduce((s, d) => s + d.revenue_energy, 0)
  const totalRevH2 = log.reduce((s, d) => s + d.revenue_h2, 0)
  const totalCost = log.reduce((s, d) => s + d.total_cost, 0)
  const totalH2 = log.reduce((s, d) => s + d.h2_produced_kg, 0)
  const totalProfit = data.total_profit

  const barData = [
    { name: 'Energia', value: +totalRevEnergy.toFixed(0), color: '#d97706' },
    { name: 'H₂ Verde', value: +totalRevH2.toFixed(0), color: '#1a7a3c' },
    { name: 'Custos', value: -Math.round(totalCost), color: '#dc2626' },
    { name: 'Lucro', value: +totalProfit.toFixed(0), color: totalProfit > 0 ? '#1a7a3c' : '#dc2626' },
  ]

  return (
    <div className="card green-accent">
      <div className="section-title">Resumo Econômico — 24h</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: 'var(--green-light)', borderRadius: '8px', padding: '12px' }}>
          <div className="label">Lucro Total</div>
          <div style={{ fontSize: '22px', fontWeight: 700, color: totalProfit > 0 ? 'var(--green)' : 'var(--red)', marginTop: '2px' }}>
            R$ {totalProfit.toFixed(0)}
          </div>
        </div>
        <div style={{ background: 'var(--bg-subtle)', borderRadius: '8px', padding: '12px' }}>
          <div className="label">H₂ Produzido</div>
          <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--green)', marginTop: '2px' }}>
            {totalH2.toFixed(1)} kg
          </div>
        </div>
        <div>
          <div className="label">Receita Energia</div>
          <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--amber)', marginTop: '2px' }}>R$ {totalRevEnergy.toFixed(0)}</div>
        </div>
        <div>
          <div className="label">Receita H₂</div>
          <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--green)', marginTop: '2px' }}>R$ {totalRevH2.toFixed(0)}</div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={90}>
        <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <XAxis dataKey="name" tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={false} tickLine={false} />
          <ReferenceLine y={0} stroke="var(--border-strong)" />
          <Bar dataKey="value" radius={[3, 3, 0, 0]} maxBarSize={44}>
            {barData.map((e, i) => <Cell key={i} fill={e.color} fillOpacity={0.8} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}