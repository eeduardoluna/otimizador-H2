import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts'

const CURTAILMENT = 120

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const price = payload.find(p => p.dataKey === 'preco')?.value
  const action = payload.find(p => p.dataKey === 'acao')?.value
  return (
    <div style={{ background: 'white', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 14px', fontSize: '12px', boxShadow: 'var(--shadow-md)' }}>
      <div style={{ color: 'var(--text-dim)', marginBottom: '6px', fontWeight: 500 }}>{label}h</div>
      {price && <div style={{ color: 'var(--amber)' }}>Preço: <strong>R$ {price}/MWh</strong></div>}
      {action !== undefined && <div style={{ color: 'var(--blue)' }}>Ação IA: <strong>{(action * 100).toFixed(0)}% eletrólise</strong></div>}
      {price <= CURTAILMENT && <div style={{ color: 'var(--red)', marginTop: '4px', fontSize: '11px' }}>⚠ Curtailment provável</div>}
    </div>
  )
}

export default function PriceChart({ data }) {
  const chartData = data?.map(d => ({ hour: d.hour, preco: Math.round(d.price_mwh), acao: d.action })) || []

  return (
    <div className="card amber-accent">
      <div className="section-title">Preço Spot + Decisão da IA</div>
      {chartData.length === 0 ? (
        <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
          <div style={{ fontSize: '28px' }}>📈</div>
          <span style={{ fontSize: '13px', color: 'var(--text-dim)' }}>Execute uma simulação</span>
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
              <XAxis dataKey="hour" tickFormatter={v => `${v}h`} tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={{ stroke: 'var(--border)' }} tickLine={false} />
              <YAxis yAxisId="price" tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `R$${v}`} />
              <YAxis yAxisId="action" orientation="right" domain={[0, 1]} tick={{ fill: 'var(--text-dim)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${(v*100).toFixed(0)}%`} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine yAxisId="price" y={CURTAILMENT} stroke="var(--red)" strokeDasharray="4 2" strokeWidth={1} />
              <Bar yAxisId="price" dataKey="preco" radius={[3, 3, 0, 0]} maxBarSize={22}>
                {chartData.map((e, i) => (
                  <Cell key={i} fill={e.preco <= CURTAILMENT ? '#fee2e2' : e.preco >= 300 ? '#fef3c7' : '#f0f4f0'} stroke={e.preco <= CURTAILMENT ? 'var(--red)' : e.preco >= 300 ? 'var(--amber)' : 'var(--border)'} strokeWidth={1} />
                ))}
              </Bar>
              <Line yAxisId="action" type="stepAfter" dataKey="acao" stroke="var(--blue)" strokeWidth={2.5} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--red)' }}>— Limite curtailment</span>
            <span style={{ fontSize: '11px', color: 'var(--blue)' }}>— Ação IA</span>
          </div>
        </>
      )}
    </div>
  )
}