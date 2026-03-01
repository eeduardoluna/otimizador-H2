import { useState, useEffect, useCallback } from 'react'
import EnergyFlowChart from './EnergyFlowChart'
import TankLevel from './TankLevel'
import PriceChart from './PriceChart'
import DecisionLog from './DecisionLog'
import ProfitSummary from './ProfitSummary'
import ComparisonChart from './ComparisonChart'
import { getDashboardCurrent, runFullEpisode, getAgentStatus } from '../services/api'

export default function Dashboard() {
  const [current, setCurrent] = useState(null)
  const [episodeData, setEpisodeData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [modelReady, setModelReady] = useState(false)
  const [error, setError] = useState(null)
  const [lastRun, setLastRun] = useState(null)

  useEffect(() => {
    getAgentStatus().then(r => setModelReady(r.data.model_loaded)).catch(() => setModelReady(false))
    getDashboardCurrent().then(r => setCurrent(r.data)).catch(() => {})
  }, [])

  const handleRunEpisode = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await runFullEpisode()
      setEpisodeData(res.data)
      setLastRun(new Date().toLocaleTimeString('pt-BR'))
    } catch (e) {
      setError('Erro ao executar episódio. Verifique se o backend está rodando.')
    } finally {
      setLoading(false)
    }
  }, [])

  return (
    <div style={{ minHeight: '100vh', padding: '24px 32px', maxWidth: '1440px', margin: '0 auto' }}>

      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: '28px', paddingBottom: '20px', borderBottom: '1px solid var(--border)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="live-dot" />
            <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 500, letterSpacing: '0.05em' }}>
              FORTALEZA, CE — SISTEMA ATIVO
            </span>
          </div>
          <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.01em' }}>
            H2 Verde <span style={{ color: 'var(--green)' }}>Optimizer</span>
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '3px' }}>
            Otimização inteligente de despacho energético via Aprendizado por Reforço
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
          <button className={`btn ${loading ? 'loading' : ''}`} onClick={handleRunEpisode} disabled={loading || !modelReady}>
            {loading ? '⟳  Simulando...' : '▶  Executar Simulação'}
          </button>
          {!modelReady && <span style={{ fontSize: '11px', color: 'var(--red)' }}>Modelo não disponível</span>}
          {lastRun && <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Última simulação: {lastRun}</span>}
        </div>
      </div>

      {error && (
        <div style={{
          background: 'var(--red-light)', border: '1px solid var(--red)', borderRadius: '8px',
          padding: '10px 14px', marginBottom: '20px', fontSize: '13px', color: 'var(--red)'
        }}>⚠ {error}</div>
      )}

      {/* Status Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        {[
          { label: 'Geração Solar', value: current ? `${current.solar_kw.toFixed(0)} kW` : '—', sub: 'Cap. 500 kW', color: 'green', accent: 'green-accent' },
          { label: 'Geração Eólica', value: current ? `${current.wind_kw.toFixed(0)} kW` : '—', sub: 'Cap. 300 kW', color: 'amber', accent: 'amber-accent' },
          { label: 'Preço Spot', value: current ? `R$ ${current.price_mwh.toFixed(0)}` : '—', sub: current?.curtailment_risk ? '⚠ Curtailment' : 'por MWh', color: 'blue', accent: 'blue-accent', warn: current?.curtailment_risk },
          { label: 'Tanque H₂', value: episodeData ? `${(episodeData.log[episodeData.log.length-1]?.tank_level*100).toFixed(1)}%` : current ? `${current.tank_level.toFixed(1)}%` : '—', sub: 'Cap. 1.000 kg', color: 'green', accent: 'green-accent' }
        ].map((c, i) => (
          <div key={i} className={`card ${c.accent}`}>
            <div className="label">{c.label}</div>
            <div className={`value ${c.color}`}>{c.value}</div>
            <div style={{ fontSize: '11px', color: c.warn ? 'var(--red)' : 'var(--text-dim)', marginTop: '4px' }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: '12px', marginBottom: '12px' }}>
        <EnergyFlowChart data={episodeData?.log} />
        <TankLevel data={episodeData?.log} />
      </div>

      {/* Charts row 2 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
        <PriceChart data={episodeData?.log} />
        <ProfitSummary data={episodeData} />
      </div>

      {/* Charts row 3 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
        <ComparisonChart episodeData={episodeData} />
        <DecisionLog data={episodeData?.log} />
      </div>

      {/* Footer */}
      <div style={{
        borderTop: '1px solid var(--border)', paddingTop: '16px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>SPIN INOVAÇÃO HACKATHON 2026</span>
        <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>PPO · Stable-Baselines3 · Open-Meteo · FastAPI · React</span>
      </div>
    </div>
  )
}