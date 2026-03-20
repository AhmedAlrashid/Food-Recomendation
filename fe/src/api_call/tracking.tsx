import { authenticatedFetch } from './authUtils'

const dbUrl = process.env.NEXT_PUBLIC_BACKEND_CALL_API ?? process.env.BACKEND_CALL_API ?? "http://localhost:8000"

export async function recordClick(businessId: string, lat?: number, lng?: number): Promise<any> {
	try {
		const response = await authenticatedFetch(`${dbUrl}/tracking/click`, {
			method: 'POST',
			body: JSON.stringify({
				business_id: businessId,
				lat: lat || null,
				lng: lng || null
			})
		})
		
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: 'Failed to record click' }))
			throw new Error(errorData.detail || `Error: ${response.status}`)
		}
		
		const data = await response.json()
		console.log("click recorded:", data)
		return data
	} catch (err) {
		console.error("click recording error:", err)
		throw err
	}
}

export async function recordLocation(lat: number, lng: number, city?: string, state?: string, country?: string): Promise<any> {
	try {
		const response = await authenticatedFetch(`${dbUrl}/tracking/location`, {
			method: 'POST',
			body: JSON.stringify({
				lat,
				lng,
				city: city || null,
				state: state || null,
				country: country || null
			})
		})
		
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: 'Failed to record location' }))
			throw new Error(errorData.detail || `Error: ${response.status}`)
		}
		
		const data = await response.json()
		console.log("location recorded:", data)
		return data
	} catch (err) {
		console.error("location recording error:", err)
		throw err
	}
}

// Geolocation utility function to get user location and city
export async function getCurrentLocationAndCity(): Promise<{lat: number, lng: number, city?: string, state?: string, country?: string}> {
	return new Promise((resolve, reject) => {
		if (!navigator.geolocation) {
			reject(new Error('Geolocation is not supported by this browser'))
			return
		}

		navigator.geolocation.getCurrentPosition(
			async (position) => {
				const lat = position.coords.latitude
				const lng = position.coords.longitude
				
				try {
					// Try to get city name using reverse geocoding (you can replace this with your preferred service)
					// For now, just return coordinates
					resolve({ lat, lng })
				} catch (err) {
					// If geocoding fails, just return coordinates
					resolve({ lat, lng })
				}
			},
			(error) => {
				console.error('Geolocation error:', error)
				reject(error)
			},
			{ 
				enableHighAccuracy: true,
				timeout: 10000,
				maximumAge: 300000 // Cache for 5 minutes
			}
		)
	})
}

export async function getUserClicks(limit: number = 50, skip: number = 0): Promise<any> {
	try {
		const response = await authenticatedFetch(`${dbUrl}/tracking/clicks?limit=${limit}&skip=${skip}`)
		
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: 'Failed to get clicks' }))
			throw new Error(errorData.detail || `Error: ${response.status}`)
		}
		
		const data = await response.json()
		return data
	} catch (err) {
		console.error("get clicks error:", err)
		throw err
	}
}

export async function recordSwipe(businessId: string): Promise<any> {
    try {
        const response = await authenticatedFetch(`${dbUrl}/recommendations/swipe`, {
            method: 'POST',
            body: JSON.stringify({ business_id: businessId })
        })
        if (!response.ok) throw new Error(`Error: ${response.status}`)
        return await response.json()
    } catch (err) {
        console.error("swipe recording error:", err)
    }
}

export async function getUserLocations(limit: number = 50, skip: number = 0): Promise<any> {
	try {
		const response = await authenticatedFetch(`${dbUrl}/tracking/locations?limit=${limit}&skip=${skip}`)
		
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: 'Failed to get locations' }))
			throw new Error(errorData.detail || `Error: ${response.status}`)
		}
		
		const data = await response.json()
		return data
	} catch (err) {
		console.error("get locations error:", err)
		throw err
	}
}

export async function getCurrentCity(): Promise<any> {
	try {
		const response = await authenticatedFetch(`${dbUrl}/tracking/current-city`)
		
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: 'Failed to get current city' }))
			throw new Error(errorData.detail || `Error: ${response.status}`)
		}
		
		const data = await response.json()
		return data
	} catch (err) {
		console.error("get current city error:", err)
		throw err
	}
}