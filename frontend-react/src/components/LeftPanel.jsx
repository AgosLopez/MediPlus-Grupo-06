import { useState, useEffect } from 'react'
import DynamicForm from './DynamicForm'
import { fetchModels, executeOperation } from '../api'
import { IconSearch, IconPlus, IconEdit, IconTrash, IconFilter, IconZap } from './Icons'

const OPERATIONS = [
  { value: 'read',   label: 'Consultar',  Icon: IconSearch },
  { value: 'create', label: 'Crear',      Icon: IconPlus   },
  { value: 'update', label: 'Actualizar', Icon: IconEdit   },
  { value: 'delete', label: 'Eliminar',   Icon: IconTrash  },
]

export default function LeftPanel({ onResults, setLoading }) {
  const [models, setModels]         = useState({})
  const [operation, setOperation]   = useState('read')
  const [model, setModel]           = useState('')
  const [formData, setFormData]     = useState({})
  const [filterData, setFilterData] = useState({})
  const [error, setError]           = useState('')

  useEffect(() => {
    fetchModels()
      .then(m => { setModels(m); setModel(Object.keys(m)[0] || '') })
      .catch(() => setError('No se pudo conectar al backend'))
  }, [])

  useEffect(() => { setFormData({}); setFilterData({}) }, [model, operation])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const strip = obj => Object.fromEntries(
        Object.entries(obj).filter(([, v]) => v !== '' && v !== null && v !== undefined)
      )
      const result = await executeOperation({
        operation,
        model,
        data:   ['create', 'update'].includes(operation) ? strip(formData)   : undefined,
        filter: ['read', 'update', 'delete'].includes(operation) ? strip(filterData) : undefined,
      })
      onResults(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const schema   = models[model] || {}
  const showFilter = ['read', 'update', 'delete'].includes(operation)
  const showData   = ['create', 'update'].includes(operation)

  const fieldsFilter = (schema.fields_filter || []).map(f => ({ ...f, required: false }))

  const fieldsCreate = (() => {
    const all = schema.fields_create || []
    if (operation === 'create') return all.map(f => ({ ...f, required: true }))
    if (operation === 'update') return all.map(f => ({ ...f, required: false }))
    return all
  })()

  return (
    <aside className="left-panel">

      {/* Operación */}
      <div className="lp-section">
        <p className="lp-label">Operación</p>
        <div className="op-grid">
          {OPERATIONS.map(({ value, label, Icon }) => (
            <button
              key={value}
              type="button"
              className={`op-btn ${operation === value ? 'op-active' : ''}`}
              onClick={() => setOperation(value)}
            >
              <Icon />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Modelo */}
      <div className="lp-section">
        <p className="lp-label">Modelo</p>
        <div className="model-tabs">
          {Object.keys(models).map(m => (
            <button
              key={m}
              type="button"
              className={`model-tab ${model === m ? 'model-tab--active' : ''}`}
              onClick={() => setModel(m)}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Formulario */}
      <form className="lp-form" onSubmit={handleSubmit}>

        {showFilter && (
          <div className="lp-form-group">
            <div className="lp-form-header">
              <IconFilter />
              <span>
                {operation === 'read'   ? 'Filtro (opcional)' :
                 operation === 'delete' ? 'Identificar registro' :
                                          'Filtro — registro a actualizar'}
              </span>
            </div>
            <DynamicForm
              fields={fieldsFilter}
              values={filterData}
              onChange={setFilterData}
              prefix="filter"
            />
          </div>
        )}

        {showData && (
          <div className="lp-form-group">
            {operation === 'update' && (
              <div className="lp-form-header lp-form-header--data">
                <IconEdit />
                <span>Nuevos valores</span>
              </div>
            )}
            <DynamicForm
              fields={fieldsCreate}
              values={formData}
              onChange={setFormData}
              prefix="data"
            />
          </div>
        )}

        {error && <p className="form-error">{error}</p>}

        <div className="lp-footer">
          <button className="btn-execute" type="submit">
            <IconZap />
            Ejecutar en todos los motores
          </button>
        </div>
      </form>

    </aside>
  )
}
