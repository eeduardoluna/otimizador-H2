import { AreaChart, Area, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'white', border: '1px solid var(--border)', borderRadius: '8px',
      padding: '10px 14px', fontSize: '12px', boxShadow: 'var(--shadow-md)'
    }}>
      <div style={{ color: 'var(--text-dim)', marginBottom: '6px', fontWeight: 500 }}>{label}h</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color, marginBottom: '2px' }}>
          {p.name}: <strong>{p.value?.toFixed(1)} kW</strong>
        </div>
      ))}
    </div>
  )
}

export default function EnergyFlowChart({ data }) {
  const chartData = data?.map(d => ({
    hour: d.hour,
    Solar: d.solar_kw,
    Eólica: d.wind_kw,
    Eletrólise: d.energy_to_electrolysis_kw,
  })) || []

  return (
    <div className="card green-accent">
      <div className="section-title">Fluxo de Energia — 24h</div>
      {chartData.length === 0 ? (
        <div style={{ height: '240px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
          <div style={{ fontSize: '28px' }}>⚡</div>
          <span style={{ fontSize: '13px', color: 'var(--text-dim)' }}>Execute uma simulação para visualizar</span>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id="gSolar" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1a7a3c" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#1a7a3c" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gWind" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#d97706" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#d97706" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gElec" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0369a1" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#0369a1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="hour" tickFormatter={v => `${v}h`} tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={{ stroke: 'var(--border)' }} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}kW`} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
            <Area type="monotone" dataKey="Solar" stroke="#1a7a3c" fill="url(#gSolar)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="Eólica" stroke="#d97706" fill="url(#gWind)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="Eletrólise" stroke="#0369a1" fill="url(#gElec)" strokeWidth={2} dot={false} strokeDasharray="5 3" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}