export default function DynamicForm({ fields, values, onChange, prefix }) {
  function handleChange(name, value) {
    onChange({ ...values, [name]: value })
  }

  return (
    <div className="dynamic-form">
      {fields.map(field => (
        <div key={`${prefix}-${field.name}`} className="form-field">
          <label className="field-label">
            {field.name.replace(/_/g, ' ')}
            {field.required && <span className="required">*</span>}
          </label>

          {field.type === 'select' ? (
            <select
              className="select-input"
              value={values[field.name] || ''}
              onChange={e => handleChange(field.name, e.target.value)}
            >
              <option value="">— seleccionar —</option>
              {field.options.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          ) : field.type === 'boolean' ? (
            <select
              className="select-input"
              value={values[field.name] ?? ''}
              onChange={e => handleChange(field.name, e.target.value === 'true')}
            >
              <option value="">— seleccionar —</option>
              <option value="true">Sí</option>
              <option value="false">No</option>
            </select>
          ) : (
            <input
              className="text-input"
              type={field.type === 'date' ? 'date' : field.type === 'email' ? 'email' : 'text'}
              value={values[field.name] || ''}
              onChange={e => handleChange(field.name, e.target.value)}
              placeholder={field.name}
            />
          )}
        </div>
      ))}
    </div>
  )
}
