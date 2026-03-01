import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceLine } from 'recharts'

export default function TankLevel({ data }) {
  const chartData = data?.map(d => ({
    hour: d.hour,
    nivel: +(d.tank_level * 100).toFixed(1)
  })) || []

  const lastLevel = chartData.length > 0 ? chartData[chartData.length - 1].nivel : null
  const color = lastLevel > 80 ? 'var(--amber)' : lastLevel < 15 ? 'var(--red)' : 'var(--green)'

  return (
    <div className="card green-accent" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div className="section-title" style={{ marginBottom: 0 }}>Tanque H₂</div>

      {/* Level number */}
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '36px', fontWeight: 700, color, lineHeight: 1 }}>
          {lastLevel !== null ? `${lastLevel.toFixed(1)}%` : '—'}
        </div>
        {lastLevel !== null && (
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '2px' }}>
            {(lastLevel * 10).toFixed(0)} kg / 1.000 kg
          </div>
        )}
      </div>

      {/* Tank visual */}
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div style={{
          width: '52px', height: '100px',
          border: '2px solid var(--border-strong)',
          borderRadius: '6px',
          position: 'relative',
          overflow: 'hidden',
          background: 'var(--bg-subtle)'
        }}>
          <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0,
            height: `${lastLevel || 0}%`,
            background: `linear-gradient(to top, ${color}, ${color}80)`,
            transition: 'height 0.8s ease'
          }} />
          <div style={{ position: 'absolute', top: 3, right: 4, fontSize: '8px', color: 'var(--text-dim)' }}>95%</div>
          <div style={{ position: 'absolute', bottom: 3, right: 4, fontSize: '8px', color: 'var(--text-dim)' }}>5%</div>
        </div>
      </div>

      {/* Mini chart */}
      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={70}>
          <LineChart data={chartData} margin={{ top: 0, right: 4, left: -28, bottom: 0 }}>
            <XAxis dataKey="hour" tickFormatter={v => `${v}h`} tick={{ fill: 'var(--text-dim)', fontSize: 9 }} axisLine={false} tickLine={false} interval={5} />
            <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-dim)', fontSize: 9 }} axisLine={false} tickLine={false} />
            <ReferenceLine y={95} stroke="var(--amber)" strokeDasharray="3 2" strokeWidth={1} />
            <ReferenceLine y={5} stroke="var(--red)" strokeDasharray="3 2" strokeWidth={1} />
            <Line type="monotone" dataKey="nivel" stroke="var(--green)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div style={{ height: '70px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Aguardando simulação</span>
        </div>
      )}
    </div>
  )
}