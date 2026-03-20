// Authentication utility functions
export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', token)
  }
}

export function removeToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token')
  }
}

export function isAuthenticated(): boolean {
  return getToken() !== null
}

// API call with auth header
export async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken()
  
  // Debug logging
  console.log('🔑 authenticatedFetch called with URL:', url)
  console.log('🔑 Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN')
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  // Merge existing headers if they exist
  if (options.headers) {
    const existingHeaders = new Headers(options.headers)
    existingHeaders.forEach((value, key) => {
      headers[key] = value
    })
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
    console.log('🔑 Authorization header set:', `Bearer ${token.substring(0, 20)}...`)
  } else {
    console.warn('🚨 No token available - request will be unauthenticated')
  }
  
  console.log('🔑 Final headers:', headers)
  
  return fetch(url, {
    ...options,
    headers
  })
}