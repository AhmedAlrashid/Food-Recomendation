import { setToken } from './authUtils'
import { recordLocation, getCurrentLocationAndCity } from './tracking'

const dbUrl = process.env.NEXT_PUBLIC_BACKEND_CALL_API ?? process.env.BACKEND_CALL_API ?? "http://localhost:8000"

export async function loginUser(username: string, password: string): Promise<any> {
	try {
		const formData = new URLSearchParams()
		formData.append('username', username)
		formData.append('password', password)

		const res = await fetch(`${dbUrl}/auth/login`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/x-www-form-urlencoded',
			},
			body: formData
		})
		
		if (!res.ok) {
			const errorData = await res.json().catch(() => ({ detail: 'Login failed' }))
			throw new Error(errorData.detail || `Login failed: ${res.status}`)
		}
		
		const data = await res.json()
		console.log("login response:", data)
		
		// Store token using auth utility
		if (data.access_token) {
			setToken(data.access_token)
		}
		
		// Record user location on successful login (in background)
		try {
			const locationData = await getCurrentLocationAndCity()
			await recordLocation(locationData.lat, locationData.lng, locationData.city, locationData.state, locationData.country)
		} catch (locationErr) {
			console.log("Location recording skipped:", locationErr)
			// Don't fail login if location recording fails
		}
		
		return data
	} catch (err) {
		console.error("login error:", err)
		throw err
	}
}

export async function registerUser(username: string, password: string, email?: string): Promise<any> {
	try {
		const res = await fetch(`${dbUrl}/auth/register`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				username,
				password,
				email: email || null
			})
		})
		
		if (!res.ok) {
			const errorData = await res.json().catch(() => ({ detail: 'Registration failed' }))
			throw new Error(errorData.detail || `Registration failed: ${res.status}`)
		}
		
		const data = await res.json()
		console.log("registration response:", data)
		return data
	} catch (err) {
		console.error("registration error:", err)
		throw err
	}
}