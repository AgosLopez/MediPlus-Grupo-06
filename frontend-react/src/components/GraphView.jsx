import { useMemo, useState } from 'react'

const NODE_COLORS = {
  Afiliado:      '#4C9BE8',
  Medico:        '#6EC6A0',
  Clinica:       '#E76F51',
  GrupoFamiliar: '#C77DFF',
  Medicamento:   '#F4A261',
}

function nodeLabel(n) {
  const p = n.properties
  if (p.nombre && p.apellido) return `${p.nombre} ${p.apellido}`
  if (p.nombre)               return p.nombre
  if (p.nombre_comercial)     return p.nombre_comercial
  if (p.afiliado_id)          return p.afiliado_id
  if (p.medico_id)            return p.medico_id
  if (p.clinica_id)           return p.clinica_id
  if (p.grupo_id)             return p.grupo_id
  return n.id.slice(-8)
}

function runForce(nodes, relationships, W, H) {
  if (!nodes.length) return {}

  const pos = {}
  nodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / nodes.length
    pos[n.id] = {
      x:  W / 2 + 160 * Math.cos(angle),
      y:  H / 2 + 130 * Math.sin(angle),
      vx: 0,
      vy: 0,
    }
  })

  for (let iter = 0; iter < 280; iter++) {
    // Repulsión entre nodos
    for (let a = 0; a < nodes.length; a++) {
      for (let b = a + 1; b < nodes.length; b++) {
        const pa = pos[nodes[a].id], pb = pos[nodes[b].id]
        const dx = pa.x - pb.x, dy = pa.y - pb.y
        const d  = Math.sqrt(dx * dx + dy * dy) || 0.1
        const f  = 4000 / (d * d)
        pa.vx += (f * dx) / d;  pb.vx -= (f * dx) / d
        pa.vy += (f * dy) / d;  pb.vy -= (f * dy) / d
      }
      // Atracción al centro
      const p = pos[nodes[a].id]
      p.vx += (W / 2 - p.x) * 0.008
      p.vy += (H / 2 - p.y) * 0.008
    }

    // Resorte por relaciones
    relationships.forEach(rel => {
      const s = pos[rel.source], t = pos[rel.target]
      if (!s || !t) return
      const dx = t.x - s.x, dy = t.y - s.y
      const d  = Math.sqrt(dx * dx + dy * dy) || 0.1
      const f  = (d - 130) * 0.06
      s.vx += (f * dx) / d;  t.vx -= (f * dx) / d
      s.vy += (f * dy) / d;  t.vy -= (f * dy) / d
    })

    // Aplicar velocidad con amortiguación
    nodes.forEach(n => {
      const p = pos[n.id]
      p.x += p.vx * 0.18;  p.y += p.vy * 0.18
      p.vx *= 0.75;         p.vy *= 0.75
      p.x = Math.max(40, Math.min(W - 40, p.x))
      p.y = Math.max(40, Math.min(H - 40, p.y))
    })
  }

  return pos
}

export default function GraphView({ nodes, relationships }) {
  const [hovered, setHovered] = useState(null)
  const W = 640, H = 400

  const pos = useMemo(
    () => runForce(nodes, relationships, W, H),
    [nodes, relationships]
  )

  if (!nodes.length) {
    return <p className="graph-empty">Sin nodos para mostrar.</p>
  }

  return (
    <div className="graph-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} className="graph-svg">
        <defs>
          <marker id="arr" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <polygon points="0 0, 7 3.5, 0 7" fill="#555" />
          </marker>
        </defs>

        {/* Aristas */}
        {relationships.map((rel, i) => {
          const s = pos[rel.source], t = pos[rel.target]
          if (!s || !t) return null
          const mx = (s.x + t.x) / 2, my = (s.y + t.y) / 2
          const dx = t.x - s.x,       dy = t.y - s.y
          const d  = Math.sqrt(dx * dx + dy * dy) || 1
          // Acortar línea para no solaparse con el nodo
          const R  = 24
          const x1 = s.x + (dx / d) * R, y1 = s.y + (dy / d) * R
          const x2 = t.x - (dx / d) * R, y2 = t.y - (dy / d) * R
          return (
            <g key={i}>
              <line
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#3a4a5a" strokeWidth={1.5}
                markerEnd="url(#arr)"
              />
              <text
                x={mx} y={my - 5}
                fill="#667"
                fontSize={9}
                textAnchor="middle"
                fontFamily="monospace"
              >
                {rel.type}
              </text>
            </g>
          )
        })}

        {/* Nodos */}
        {nodes.map(n => {
          const p = pos[n.id]
          if (!p) return null
          const color   = NODE_COLORS[n.label] || '#8b949e'
          const isHov   = hovered === n.id
          const lbl     = nodeLabel(n)
          const display = lbl.length > 18 ? lbl.slice(0, 17) + '…' : lbl
          return (
            <g
              key={n.id}
              style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered(null)}
            >
              <circle
                cx={p.x} cy={p.y} r={isHov ? 27 : 24}
                fill={color}
                fillOpacity={isHov ? 1 : 0.8}
                stroke={color}
                strokeWidth={isHov ? 2.5 : 1.5}
                style={{ transition: 'r 0.15s, fill-opacity 0.15s' }}
              />
              {/* Tipo (etiqueta Neo4j) */}
              <text
                x={p.x} y={p.y - 2}
                fill="white"
                fontSize={8}
                fontWeight="bold"
                textAnchor="middle"
                dominantBaseline="middle"
                pointerEvents="none"
              >
                {n.label.toUpperCase()}
              </text>
              {/* Nombre / id debajo */}
              <text
                x={p.x} y={p.y + 35}
                fill="#adbac7"
                fontSize={9}
                textAnchor="middle"
                pointerEvents="none"
              >
                {display}
              </text>

              {/* Tooltip al hover */}
              {isHov && (
                <foreignObject
                  x={p.x + 28} y={p.y - 40}
                  width={200} height={120}
                  style={{ pointerEvents: 'none' }}
                >
                  <div className="graph-tooltip">
                    <strong>{n.label}</strong>
                    {Object.entries(n.properties).slice(0, 5).map(([k, v]) => (
                      <div key={k} className="graph-tooltip-row">
                        <span className="graph-tooltip-key">{k}</span>
                        <span className="graph-tooltip-val">
                          {String(v).length > 22 ? String(v).slice(0, 21) + '…' : String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                </foreignObject>
              )}
            </g>
          )
        })}
      </svg>

      {/* Leyenda */}
      <div className="graph-legend">
        {[...new Set(nodes.map(n => n.label))].map(lbl => (
          <span key={lbl} className="graph-legend-item">
            <span
              className="graph-legend-dot"
              style={{ background: NODE_COLORS[lbl] || '#8b949e' }}
            />
            {lbl}
          </span>
        ))}
      </div>
    </div>
  )
}
