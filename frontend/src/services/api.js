export class ApiError extends Error {
  constructor(status, message, data = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

class ApiClient {
  buildUrl(endpoint, params) {
    const url = new URL(endpoint, window.location.origin)
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          url.searchParams.append(key, String(val))
        }
      })
    }
    return url.pathname + url.search
  }

  async request(endpoint, options = {}) {
    const { params, headers = {}, body, ...customConfig } = options
    const targetUrl = this.buildUrl(endpoint, params)

    const requestHeaders = new Headers(headers)
    if (!requestHeaders.has('Accept')) {
      requestHeaders.set('Accept', 'application/json')
    }

    let serializedBody = body
    if (body && typeof body === 'object' && !(body instanceof FormData)) {
      if (!requestHeaders.has('Content-Type')) {
        requestHeaders.set('Content-Type', 'application/json')
      }
      serializedBody = JSON.stringify(body)
    }

    const response = await fetch(targetUrl, {
      credentials: 'include',
      ...customConfig,
      headers: requestHeaders,
      body: serializedBody,
    })

    let responseData = null
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      responseData = await response.json().catch(() => null)
    } else {
      responseData = await response.text().catch(() => null)
    }

    if (!response.ok) {
      const errorMessage =
        (responseData && (responseData.detail || responseData.error)) ||
        `Request failed with status ${response.status}`
      throw new ApiError(response.status, errorMessage, responseData)
    }

    return responseData
  }

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' })
  }

  post(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body })
  }

  put(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', body })
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' })
  }
}

export const api = new ApiClient()

