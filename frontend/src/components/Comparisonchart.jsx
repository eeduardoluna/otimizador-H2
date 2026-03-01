import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { getComparison } from '../services/api'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'white', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 14px', fontSize: '12px', boxShadow: 'var(--shadow-md)' }}>
      <div style={{ color: 'var(--text-dim)', marginBottom: '6px', fontWeight: 500 }}>{label}h</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color, marginBottom: '2px' }}>
          {p.name}: <strong>R$ {p.value?.toFixed(0)}</strong>
        </div>
      ))}
    </div>
  )
}

export default function ComparisonChart({ episodeData }) {
  const [compData, setCompData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!episodeData) return
    setLoading(true)
    getComparison().then(r => setCompData(r.data)).catch(() => {}).finally(() => setLoading(false))
  }, [episodeData])

  const chartData = compData?.rl_agent && compData?.baseline
    ? compData.rl_agent.cumulative_series.map((item, i) => ({
        hour: item.hour,
        'IA (PPO)': item.cumulative_profit,
        'Regra Simples': compData.baseline.cumulative_series[i]?.cumulative_profit ?? 0,
      }))
    : []

  const improvement = compData?.improvement_pct

  return (
    <div className="card blue-accent">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div className="section-title" style={{ marginBottom: 0 }}>IA vs Regra Simples</div>
        {improvement != null && (
          <span style={{
            background: improvement > 0 ? 'var(--green-light)' : 'var(--red-light)',
            color: improvement > 0 ? 'var(--green)' : 'var(--red)',
            border: `1px solid ${improvement > 0 ? 'var(--green-mid)' : 'var(--red)'}`,
            borderRadius: '20px', padding: '3px 10px', fontSize: '12px', fontWeight: 600
          }}>
            {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}%
          </span>
        )}
      </div>

      {chartData.length === 0 ? (
        <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
          {loading
            ? <span style={{ fontSize: '13px', color: 'var(--blue)' }}>Calculando comparação...</span>
            : <><div style={{ fontSize: '28px' }}>📊</div><span style={{ fontSize: '13px', color: 'var(--text-dim)' }}>Execute uma simulação para comparar</span></>
          }
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
              <XAxis dataKey="hour" tickFormatter={v => `${v}h`} tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={{ stroke: 'var(--border)' }} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `R$${v}`} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
              <Line type="monotone" dataKey="IA (PPO)" stroke="var(--green)" strokeWidth={2.5} dot={false} />
              <Line type="monotone" dataKey="Regra Simples" stroke="var(--text-dim)" strokeWidth={1.5} dot={false} strokeDasharray="5 3" />
            </LineChart>
          </ResponsiveContainer>
          {compData && (
            <div style={{ display: 'flex', gap: '20px', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
              <div><div className="label">IA Total</div><div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--green)', marginTop: '2px' }}>R$ {compData.rl_agent?.total_profit?.toFixed(0)}</div></div>
              <div><div className="label">Baseline</div><div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '2px' }}>R$ {compData.baseline?.total_profit?.toFixed(0)}</div></div>
              <div><div className="label">Ganho</div><div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--green)', marginTop: '2px' }}>R$ {((compData.rl_agent?.total_profit||0)-(compData.baseline?.total_profit||0)).toFixed(0)}</div></div>
            </div>
          )}
        </>
      )}
    </div>
  )
}