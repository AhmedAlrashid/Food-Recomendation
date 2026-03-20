"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { FaHeart, FaHeartBroken, FaStar } from "react-icons/fa";
import { isAuthenticated, authenticatedFetch } from "../../src/api_call/authUtils";
import SideNavbar from "../../src/components/SideNavbar";
import { recordSwipe } from "../../src/api_call/tracking";

const dbUrl = process.env.NEXT_PUBLIC_BACKEND_CALL_API ?? "http://localhost:8000"

type Restaurant = {
  business_id: string
  name: string
  categories: string[]
  reason?: string
  remaining?: number
  photoUrl?: string
  rating?: number
  address?: string
  openNow?: boolean
}

async function fetchNextRestaurant(): Promise<Restaurant | null> {
  try {
    const res = await authenticatedFetch(`${dbUrl}/recommendations/next`)
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

async function enrichWithPlaces(name: string): Promise<Partial<Restaurant>> {
  try {
    const params = new URLSearchParams({ query: name, limit: "1", opennow: "false" })
    const res = await fetch(`${dbUrl}/places/search?${params}`)
    if (!res.ok) return {}
    const data = await res.json()
    const place = data.results?.[0]
    if (!place) return {}
    const photoRef = place.photos?.[0]?.photo_reference
    const photoUrl = photoRef
      ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference=${photoRef}&key=${process.env.NEXT_PUBLIC_GOOGLE_API_KEY}`
      : undefined
    return {
      photoUrl,
      rating: place.rating,
      address: place.formatted_address,
      openNow: place.opening_hours?.open_now,
    }
  } catch {
    return {}
  }
}

export default function SwipePage() {
  const router = useRouter()
  const [current, setCurrent] = useState<Restaurant | null>(null)
  const [next, setNext] = useState<Restaurant | null>(null)
  const [direction, setDirection] = useState<"left" | "right" | null>(null)
  const [isAnimating, setIsAnimating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [done, setDone] = useState(false)

  // Client-side dedup — track every ID we've shown this session
  const seenIds = useRef<Set<string>>(new Set())
  // Pre-fetched queue of raw (unenriched) restaurants
  const rawQueue = useRef<Restaurant[]>([])
  // Whether a background refill is already running
  const refilling = useRef(false)

  useEffect(() => {
    if (!isAuthenticated()) { router.push("/"); return }
    loadInitial()
  }, [router])

  // Fetch 3 raw restaurants in parallel, returns a promise so callers can await it
  const refillQueue = useCallback(async () => {
    if (refilling.current) return
    refilling.current = true
    try {
      const results = await Promise.all([
        fetchNextRestaurant(),
        fetchNextRestaurant(),
        fetchNextRestaurant(),
      ])
      for (const r of results) {
        if (r && !seenIds.current.has(r.business_id)) {
          seenIds.current.add(r.business_id)
          rawQueue.current.push(r)
        }
      }
    } finally {
      refilling.current = false
    }
  }, [])

  // Pop one raw restaurant from queue, enriching with Places
  const popEnriched = useCallback(async (): Promise<Restaurant | null> => {
    // Ensure queue has items
    if (rawQueue.current.length === 0) {
      refilling.current = false // reset lock so refill can run
      await refillQueue()
    }
    const r = rawQueue.current.shift()
    if (!r) return null
    // Kick off background refill if queue is getting low
    if (rawQueue.current.length < 2) {
      refilling.current = false
      refillQueue()
    }
    const enriched = await enrichWithPlaces(r.name)
    return { ...r, ...enriched }
  }, [refillQueue])

  const loadInitial = async () => {
    setLoading(true)
    // Fully await the first refill so queue is populated
    refilling.current = false
    await refillQueue()
    if (rawQueue.current.length === 0) {
      setDone(true)
      setLoading(false)
      return
    }
    // Enrich current and next in parallel
    const [c, n] = await Promise.all([popEnriched(), popEnriched()])
    if (!c) { setDone(true); setLoading(false); return }
    setCurrent(c)
    setNext(n)
    setLoading(false)
    // Pre-fill queue for future swipes
    refilling.current = false
    refillQueue()
  }

  const handleSwipe = useCallback((dir: "left" | "right") => {
    if (!current || isAnimating) return

    // Record right swipe immediately
    if (dir === "right") {
      recordSwipe(current.business_id).catch(console.error)
    }

    setIsAnimating(true)
    setDirection(dir)

    setTimeout(() => {
      // Promote next card to current
      setCurrent(next ?? null)
      setNext(null)
      setDirection(null)
      setIsAnimating(false)

      if (!next) {
        setDone(true)
        return
      }

      // Fetch the card after next in background
      popEnriched().then(r => setNext(r))
      // Keep queue topped up
      refillQueue()
    }, 300)
  }, [current, next, isAnimating, popEnriched, refillQueue])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") handleSwipe("left")
      if (e.key === "ArrowRight") handleSwipe("right")
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [handleSwipe])

  if (loading) {
    return (
      <SideNavbar>
        <div style={containerStyle}>
          <div style={{ fontSize: 18, color: "#6b7280" }}>Loading restaurants...</div>
        </div>
      </SideNavbar>
    )
  }

  if (done || !current) {
    return (
      <SideNavbar>
        <div style={containerStyle}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎉</div>
            <h2 style={{ margin: "0 0 8px", color: "#111827" }}>You've seen everything!</h2>
            <p style={{ color: "#6b7280", marginBottom: 24 }}>Keep swiping right to improve your recommendations.</p>
            <button onClick={() => router.push("/home")} style={{
              padding: "12px 24px", background: "#3b82f6", color: "#fff",
              border: "none", borderRadius: 8, cursor: "pointer", fontSize: 15, fontWeight: 600,
            }}>Back to Home</button>
          </div>
        </div>
      </SideNavbar>
    )
  }

  return (
    <SideNavbar>
      <div style={containerStyle}>
        <div style={stackStyle}>
          {next && (
            <div style={{ ...cardStyle, ...nextCardStyle }}>
              <div style={imageContainerStyle}>
                {next.photoUrl
                  ? <img src={next.photoUrl} alt={next.name} style={imageStyle} />
                  : <div style={imagePlaceholderStyle}>🍽️</div>
                }
              </div>
              <div style={contentStyle}>
                <h2 style={titleStyle}>{next.name}</h2>
                <div style={ratingStyle}>
                  <span>{next.categories.slice(0, 2).join(" · ")}</span>
                </div>
              </div>
            </div>
          )}

          <div style={{
            ...cardStyle,
            ...(direction === "left" ? swipeLeft : {}),
            ...(direction === "right" ? swipeRight : {}),
          }}>
            <button onClick={() => handleSwipe("left")} style={leftButtonStyle}>
              <FaHeartBroken size={22} />
            </button>
            <button onClick={() => handleSwipe("right")} style={rightButtonStyle}>
              <FaHeart size={22} />
            </button>

            {direction === "right" && (
              <div style={{ ...overlayStyle, left: 20, background: "rgba(40,167,69,0.85)" }}>LIKE</div>
            )}
            {direction === "left" && (
              <div style={{ ...overlayStyle, right: 20, background: "rgba(220,53,69,0.85)" }}>NOPE</div>
            )}

            <div style={imageContainerStyle}>
              {current.photoUrl
                ? <img src={current.photoUrl} alt={current.name} style={imageStyle} />
                : <div style={imagePlaceholderStyle}>🍽️</div>
              }
              {current.openNow != null && (
                <span style={{
                  position: "absolute", bottom: 12, left: 12,
                  background: current.openNow ? "#16a34a" : "#dc2626",
                  color: "#fff", padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 600,
                }}>
                  {current.openNow ? "Open now" : "Closed"}
                </span>
              )}
            </div>

            <div style={contentStyle}>
              <h2 style={titleStyle}>{current.name}</h2>
              <div style={ratingStyle}>
                {current.rating && (
                  <>
                    <FaStar size={15} color="#f5c518" />
                    <span style={{ fontWeight: 600 }}>{current.rating.toFixed(1)}</span>
                    <span style={{ color: "#9ca3af" }}>·</span>
                  </>
                )}
                <span>{current.categories.slice(0, 3).join(" · ")}</span>
              </div>
              {current.address && (
                <p style={descriptionStyle}>📍 {current.address}</p>
              )}
            </div>
          </div>
        </div>

        <p style={{ position: "absolute", bottom: 24, color: "#9ca3af", fontSize: 13 }}>
          ← Pass &nbsp;|&nbsp; Like → &nbsp;·&nbsp; or use arrow keys
        </p>
      </div>
    </SideNavbar>
  )
}

const containerStyle: React.CSSProperties = { height: "100vh", display: "flex", justifyContent: "center", alignItems: "center", background: "#f5f5f5", position: "relative" }
const stackStyle: React.CSSProperties = { position: "relative", width: "min(600px, 90vw)", height: "520px" }
const cardStyle: React.CSSProperties = { position: "absolute", width: "100%", height: "100%", background: "white", borderRadius: 20, boxShadow: "0 20px 40px rgba(0,0,0,0.12)", display: "flex", flexDirection: "column", overflow: "hidden", transition: "transform 0.3s ease, opacity 0.3s ease" }
const imageContainerStyle: React.CSSProperties = { position: "relative", width: "100%", height: "62%", background: "#f3f4f6", flexShrink: 0 }
const imageStyle: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover" }
const imagePlaceholderStyle: React.CSSProperties = { width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 48 }
const contentStyle: React.CSSProperties = { padding: "18px 24px", display: "flex", flexDirection: "column", gap: 8 }
const titleStyle: React.CSSProperties = { margin: 0, fontSize: 22, fontWeight: 700, color: "#111827" }
const descriptionStyle: React.CSSProperties = { margin: 0, fontSize: 14, color: "#6b7280", lineHeight: 1.5, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }
const ratingStyle: React.CSSProperties = { display: "flex", alignItems: "center", gap: 6, fontSize: 14, color: "#374151" }
const nextCardStyle: React.CSSProperties = { transform: "scale(0.95) translateY(20px)", opacity: 0.75 }
const swipeLeft: React.CSSProperties = { transform: "translateX(-600px) rotate(-20deg)", opacity: 0 }
const swipeRight: React.CSSProperties = { transform: "translateX(600px) rotate(20deg)", opacity: 0 }
const baseButtonStyle: React.CSSProperties = { position: "absolute", top: "42%", transform: "translateY(-50%)", zIndex: 10, border: "none", borderRadius: "50%", width: 56, height: 56, cursor: "pointer", display: "flex", justifyContent: "center", alignItems: "center", boxShadow: "0 4px 12px rgba(0,0,0,0.2)" }
const leftButtonStyle: React.CSSProperties = { ...baseButtonStyle, left: 16, background: "rgba(220,53,69,0.9)", color: "white" }
const rightButtonStyle: React.CSSProperties = { ...baseButtonStyle, right: 16, background: "rgba(40,167,69,0.9)", color: "white" }
const overlayStyle: React.CSSProperties = { position: "absolute", top: 20, zIndex: 20, padding: "8px 16px", borderRadius: 8, color: "#fff", fontSize: 20, fontWeight: 800, letterSpacing: 2 }