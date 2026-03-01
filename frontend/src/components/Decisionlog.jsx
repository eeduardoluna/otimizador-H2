export default function DecisionLog({ data }) {
  const log = data || []

  return (
    <div className="card">
      <div className="section-title">Raciocínio da IA — Hora a Hora</div>
      {log.length === 0 ? (
        <div style={{ height: '260px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
          <div style={{ fontSize: '28px' }}>🤖</div>
          <span style={{ fontSize: '13px', color: 'var(--text-dim)' }}>Execute uma simulação para ver as decisões</span>
        </div>
      ) : (
        <div style={{ height: '300px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {log.map((step, i) => {
            const isElectrolysis = step.electrolyzer_on
            const isSelling = step.action < 0.1
            const accentColor = isElectrolysis ? 'var(--green)' : isSelling ? 'var(--amber)' : 'var(--blue)'
            const bgColor = isElectrolysis ? 'var(--green-light)' : isSelling ? 'var(--amber-light)' : 'var(--blue-light)'

            return (
              <div key={i} style={{
                display: 'flex', gap: '10px', alignItems: 'flex-start',
                padding: '8px 12px', background: bgColor,
                borderRadius: '6px', borderLeft: `3px solid ${accentColor}`,
                fontSize: '12px',
              }}>
                <div style={{ color: accentColor, fontWeight: 700, minWidth: '28px', fontFamily: 'var(--font-mono)' }}>
                  {String(step.hour).padStart(2, '0')}h
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '2px' }}>
                    <span style={{ fontWeight: 600, color: accentColor }}>
                      {isElectrolysis ? '⚡ Eletrólise' : '🔌 Rede elétrica'}
                    </span>
                    <span style={{ color: 'var(--text-secondary)' }}>R${step.price_mwh?.toFixed(0)}/MWh</span>
                    <span style={{ color: step.profit > 0 ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>
                      {step.profit > 0 ? '+' : ''}R${step.profit?.toFixed(0)}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-dim)', fontSize: '11px' }}>
                    {step.total_gen_kw?.toFixed(0)}kW gerados · {step.h2_produced_kg?.toFixed(2)}kg H₂ · tanque {(step.tank_level*100)?.toFixed(1)}%
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}