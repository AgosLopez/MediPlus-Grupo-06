import { useState } from 'react'
import GraphView from './GraphView'
import { IconTerminal } from './Icons'

const DB_ENGINES = ['neo4j', 'mongodb', 'redis', 'cassandra']

const DB_META = {
  neo4j:     { label: 'Neo4j',     color: '#4C9BE8', format: 'Cypher' },
  mongodb:   { label: 'MongoDB',   color: '#6EC6A0', format: 'MQL'    },
  redis:     { label: 'Redis',     color: '#E76F51', format: 'CLI'    },
  cassandra: { label: 'Cassandra', color: '#C77DFF', format: 'CQL'    },
}

function StatusBadge({ status }) {
  const map = {
    ok:             { label: 'OK',  cls: 'badge-ok'  },
    error:          { label: 'ERR', cls: 'badge-err' },
    unavailable:    { label: 'OFF', cls: 'badge-off' },
    not_applicable: { label: 'N/A', cls: 'badge-na'  },
  }
  const s = map[status] || { label: status, cls: 'badge-off' }
  return <span className={`badge ${s.cls}`}>{s.label}</span>
}

function EnfermedadModal({ item, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <span className="modal-title">{item.nombre || 'Detalle'}</span>
          <button className="modal-close" onClick={onClose}>✕ Cerrar</button>
        </div>
        <div className="modal-body">
          {Object.entries(item).map(([k, v]) => (
            <div key={k} className="modal-row">
              <span className="modal-key">{k}</span>
              <span className="modal-val">
                {v === null || v === undefined
                  ? <span className="db-card-muted">—</span>
                  : typeof v === 'object'
                    ? <span className="db-card-nested">{JSON.stringify(v)}</span>
                    : String(v)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function MongoCard({ doc }) {
  const [modalItem, setModalItem] = useState(null)

  return (
    <>
      <div className="db-card mongo-card">
        {Object.entries(doc).map(([k, v]) => {
          const isObj = typeof v === 'object' && v !== null && !Array.isArray(v)
          const isArr = Array.isArray(v)
          return (
            <div key={k} className="db-card-row">
              <span className="db-card-key">{k}</span>
              <span className="db-card-val">
                {isObj ? <span className="db-card-nested">{JSON.stringify(v)}</span>
               : isArr ? (
                  v.length === 0
                    ? <span className="db-card-muted">[ vacío ]</span>
                    : <span className="db-card-tags">
                        {v.map((item, i) => {
                          const isItemObj = typeof item === 'object' && item !== null
                          const label = isItemObj
                            ? (item.nombre || item.name || `Item ${i + 1}`)
                            : String(item)
                          return (
                            <span key={i} className="db-card-tag-row">
                              <span className="db-card-tag">{label}</span>
                              {isItemObj && (
                                <button
                                  className="db-card-tag-btn"
                                  onClick={() => setModalItem(item)}
                                  title="Ver detalle"
                                >+</button>
                              )}
                            </span>
                          )
                        })}
                      </span>
                )
               : String(v)}
              </span>
            </div>
          )
        })}
      </div>
      {modalItem && <EnfermedadModal item={modalItem} onClose={() => setModalItem(null)} />}
    </>
  )
}

function MongoResult({ data }) {
  if (!data) return null
  if (Array.isArray(data)) {
    if (!data.length) return <p className="db-empty">Sin documentos encontrados</p>
    return <div className="db-card-list">{data.map((d, i) => <MongoCard key={i} doc={d} />)}</div>
  }
  if ('matched' in data || 'modified' in data || 'deleted' in data) return <MutationResult data={data} />
  return <MongoCard doc={data} />
}

function RedisResult({ data }) {
  if (!data) return null
  if (Array.isArray(data)) {
    if (!data.length) return <p className="db-empty">Sin datos en Redis</p>
    return (
      <div className="redis-ranking">
        {data.map((item, i) => (
          <div key={i} className="redis-rank-row">
            <span className="redis-rank-pos">#{i + 1}</span>
            <span className="redis-rank-id">{item.medico_id ?? JSON.stringify(item)}</span>
            {item.consultas !== undefined && (
              <span className="redis-rank-score">{item.consultas} consultas</span>
            )}
          </div>
        ))}
      </div>
    )
  }
  if (typeof data === 'object') {
    const entries = Object.entries(data)
    if (!entries.length) return <p className="db-empty">Sin claves encontradas</p>
    return (
      <div className="redis-kv-list">
        {entries.map(([k, v]) => {
          const isHash = typeof v === 'object' && v !== null
          return (
            <div key={k} className="redis-kv-block">
              <div className="redis-kv-key">{k}</div>
              {isHash ? (
                <div className="redis-kv-hash">
                  {Object.entries(v).map(([hk, hv]) => (
                    <div key={hk} className="redis-kv-hash-row">
                      <span className="redis-kv-hkey">{hk}</span>
                      <span className="redis-kv-hval">{hv}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="redis-kv-val">{String(v)}</div>
              )}
            </div>
          )
        })}
      </div>
    )
  }
  return <pre className="code-block data-block">{JSON.stringify(data, null, 2)}</pre>
}

function CassandraResult({ data }) {
  if (!data) return null
  if (Array.isArray(data)) {
    if (!data.length) return <p className="db-empty">Sin filas encontradas</p>
    const cols = Object.keys(data[0])
    return (
      <div className="cass-table-wrap">
        <table className="cass-table">
          <thead>
            <tr>{cols.map(c => <th key={c}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i}>
                {cols.map(c => (
                  <td key={c}>
                    {typeof row[c] === 'object' && row[c] !== null
                      ? JSON.stringify(row[c])
                      : String(row[c] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }
  if ('updated' in data || 'deleted' in data) return <MutationResult data={data} />
  return <pre className="code-block data-block">{JSON.stringify(data, null, 2)}</pre>
}

function MutationResult({ data }) {
  return (
    <div className="db-mutation-result">
      {Object.entries(data).map(([k, v]) => (
        <div key={k} className="db-mutation-card">
          <span className="db-mutation-val">{String(v)}</span>
          <span className="db-mutation-label">{k}</span>
        </div>
      ))}
    </div>
  )
}

function ResultBlock({ engine, result }) {
  if (!result) return (
    <div className="result-empty">
      <div className="empty-icon-wrap">
        <IconTerminal />
      </div>
      <span className="empty-terminal">&gt;_</span>
      <p className="empty-title">Ejecuta una operación para ver resultados</p>
      <p className="empty-sub">Selecciona un modelo y presiona ejecutar</p>
    </div>
  )

  const meta    = DB_META[engine]
  const isGraph = engine === 'neo4j' && result.status === 'ok' && result.data?.nodes !== undefined

  return (
    <div className="result-block">

      <div className="result-header">
        <span className="result-engine-dot" style={{ background: meta.color }} />
        <span className="result-engine" style={{ color: meta.color }}>{meta.label}</span>
        <StatusBadge status={result.status} />
        <span className="result-format">{meta.format}</span>
        {isGraph && (
          <span className="result-count" style={{ color: meta.color }}>
            {result.data.nodes.length} nodos · {result.data.relationships.length} relaciones
          </span>
        )}
      </div>

      {result.query && (
        <div className="result-section">
          <p className="result-label">Query ejecutada</p>
          <pre className="code-block query-block">{result.query}</pre>
        </div>
      )}

      {result.error && (
        <div className="result-section">
          <p className="result-label">Error</p>
          <pre className="code-block error-block">{result.error}</pre>
        </div>
      )}

      {result.status === 'not_applicable' && result.data?.msg && (
        <div className="result-section">
          <p className="db-na-msg">{result.data.msg}</p>
        </div>
      )}

      {result.status === 'ok' && result.data !== null && result.data !== undefined && (
        <div className="result-section">
          <p className="result-label">Resultado</p>
          {isGraph            ? <GraphView nodes={result.data.nodes} relationships={result.data.relationships} />
          : engine === 'mongodb'   ? <MongoResult data={result.data} />
          : engine === 'redis'     ? <RedisResult data={result.data} />
          : engine === 'cassandra' ? <CassandraResult data={result.data} />
          : <pre className="code-block data-block">{JSON.stringify(result.data, null, 2)}</pre>}
        </div>
      )}
    </div>
  )
}

export default function ResultsPanel({ results, activeTab, setActiveTab, loading }) {
  return (
    <main className="results-panel">

      <div className="tab-bar">
        {DB_ENGINES.map(db => {
          const meta   = DB_META[db]
          const status = results?.[db]?.status
          const isActive = activeTab === db
          return (
            <button
              key={db}
              className={`tab-btn ${isActive ? 'tab-active' : ''}`}
              style={isActive ? { borderBottomColor: meta.color } : {}}
              onClick={() => setActiveTab(db)}
            >
              <span
                className="tab-dot"
                style={{ background: status === 'ok' ? meta.color : '#30363d' }}
              />
              <span style={isActive ? { color: meta.color } : {}}>{meta.label}</span>
              {status && <StatusBadge status={status} />}
            </button>
          )
        })}
      </div>

      <div className="results-content">
        {loading ? (
          <div className="loading-state">
            <div className="spinner" />
            <span>Ejecutando en todos los motores…</span>
          </div>
        ) : (
          <ResultBlock engine={activeTab} result={results?.[activeTab]} />
        )}
      </div>

      {results && !loading && (
        <div className="results-summary">
          {DB_ENGINES.map(db => (
            <div
              key={db}
              className={`summary-card ${activeTab === db ? 'summary-active' : ''}`}
              onClick={() => setActiveTab(db)}
              style={{ borderLeftColor: DB_META[db].color }}
            >
              <span className="summary-name">{DB_META[db].label}</span>
              <StatusBadge status={results[db]?.status} />
              {results[db]?.status === 'ok' && Array.isArray(results[db]?.data) && (
                <span className="summary-count">{results[db].data.length} reg.</span>
              )}
              {results[db]?.status === 'ok' && results[db]?.data?.nodes && (
                <span className="summary-count">{results[db].data.nodes.length} nodos</span>
              )}
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
