async function safeFetch(url, options) {
  const res = await fetch(url, options)
  const text = await res.text()
  if (!text) throw new Error('Respuesta vacia del servidor')
  try {
    return JSON.parse(text)
  } catch {
    throw new Error('Respuesta invalida del servidor')
  }
}

export async function fetchHealth() {
  return safeFetch('/api/health')
}

export async function fetchModels() {
  return safeFetch('/api/models')
}

export async function executeOperation({ operation, model, data, filter }) {
  const body = await safeFetch('/api/operation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operation, model, data, filter }),
  })
  return body
}
