import { authenticatedFetch } from './authUtils'

const dbUrl = process.env.NEXT_PUBLIC_BACKEND_CALL_API ?? process.env.BACKEND_CALL_API ?? "http://localhost:8000"
console.log('API Base URL:', dbUrl)

export async function getRandomRestaurants(count: number = 20): Promise<any> {
	try {
		const url = `${dbUrl}/recommendations/random?count=${count}`
		console.log('Fetching random restaurants from:', url)
		
		const response = await authenticatedFetch(url)
		console.log('Random restaurants response status:', response.status)
		
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch restaurants' }))
			console.error('Random restaurants error response:', errorData)
			throw new Error(errorData.detail || `Error: ${response.status}`)
		}
		
		const data = await response.json()
		console.log("random restaurants fetched:", data)
		return data
	} catch (err) {
		console.error("random restaurants error:", err)
		throw err
	}
}

export async function getTop20Recommendations(): Promise<any> {
	try {
		const url = `${dbUrl}/recommendations/top10`
		console.log('Fetching top 20 recommendations from:', url)
		
		const response = await authenticatedFetch(url)
		console.log('Top 20 recommendations response status:', response.status)
		
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch recommendations' }))
			console.error('Top 20 recommendations error response:', errorData)
			throw new Error(errorData.detail || `Error: ${response.status}`)
		}
		
		const data = await response.json()
		console.log("top 20 recommendations fetched:", data)
		return data
	} catch (err) {
		console.error("recommendations error:", err)
		throw err
	}
}

export async function getPersonalizedRecommendations(count: number = 10): Promise<any> {
	try {
		const response = await authenticatedFetch(`${dbUrl}/recommendations/?top_k=${count}`)
		
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch personalized recommendations' }))
			throw new Error(errorData.detail || `Error: ${response.status}`)
		}
		
		const data = await response.json()
		console.log("personalized recommendations fetched:", data)
		return data
	} catch (err) {
		console.error("personalized recommendations error:", err)
		throw err
	}
}