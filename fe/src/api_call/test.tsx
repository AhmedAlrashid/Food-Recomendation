const dbUrl = process.env.BACKEND_CALL_API ?? "http://localhost:4000"

export async function getBackendRoot(): Promise<any> {
	try {
		const res = await fetch(`${dbUrl}/`)
		if (!res.ok) throw new Error(`Request failed: ${res.status}`)
		const data = await res.json()
		console.log("backend response:", data)
		return data
	} catch (err) {
		console.error("backend call error:", err)
		throw err
	}
}