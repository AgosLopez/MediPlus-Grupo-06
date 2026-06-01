import { useState, useEffect } from 'react'
import LeftPanel from './components/LeftPanel'
import ResultsPanel from './components/ResultsPanel'
import { fetchHealth } from './api'
import './App.css'

const DB_ENGINES = ['neo4j', 'mongodb', 'redis', 'cassandra']

const DB_COLORS = {
  neo4j:     '#4C9BE8',
  mongodb:   '#6EC6A0',
  redis:     '#E76F51',
  cassandra: '#C77DFF',
}

export default function App() {
  const [results, setResults] = useState(null)
  const [activeTab, setActiveTab] = useState('neo4j')
  const [loading, setLoading] = useState(false)
  const [health, setHealth] = useState({})

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {})
    const interval = setInterval(() => {
      fetchHealth().then(setHealth).catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  function handleResults(data) {
    setResults(data)
    const firstOk = DB_ENGINES.find(db => data[db]?.status === 'ok')
    if (firstOk) setActiveTab(firstOk)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-brand">
          <div className="app-logo-circle">M</div>
          <div className="app-brand-text">
            <span className="app-logo">MediPlus</span>
            <span className="app-subtitle">Panel de Operaciones</span>
          </div>
        </div>

        <div className="health-bar">
          {DB_ENGINES.map(db => {
            const ok = health[db] === 'ok'
            return (
              <span
                key={db}
                className="health-pill"
                style={{
                  color:       ok ? DB_COLORS[db] : '#555',
                  borderColor: ok ? DB_COLORS[db] : '#333',
                  background:  ok ? `${DB_COLORS[db]}18` : '#1a1a1a',
                }}
              >
                <span
                  className="health-dot-led"
                  style={{ background: ok ? DB_COLORS[db] : '#444' }}
                />
                {db.toUpperCase()}
              </span>
            )
          })}
        </div>
      </header>

      <div className="app-body">
        <LeftPanel onResults={handleResults} setLoading={setLoading} />
        <ResultsPanel
          results={results}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          loading={loading}
        />
      </div>
    </div>
  )
}
