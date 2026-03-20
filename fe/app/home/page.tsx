"use client"
import React, { useEffect, useState, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import { isAuthenticated, removeToken, authenticatedFetch } from "../../src/api_call/authUtils"
import SideNavbar from "../../src/components/SideNavbar"
import { getRandomRestaurants, getTop20Recommendations } from "../../src/api_call/recommendations"
import { recordClick } from "../../src/api_call/tracking"

const dbUrl = process.env.NEXT_PUBLIC_BACKEND_CALL_API ?? "http://localhost:8000"

type Restaurant = {
  business_id: string
  name: string
  categories: string[]
  score?: number
  reason?: string
}

type PlaceDetails = {
  place_id?: string
  name?: string
  formatted_address?: string
  rating?: number
  user_ratings_total?: number
  price_level?: number
  photos?: { photo_reference: string }[]
  website?: string
  phone_number?: string
  opening_hours?: { weekday_text?: string[]; open_now?: boolean }
  reviews?: { author_name: string; rating: number; text: string; relative_time_description: string }[]
  google_maps_url?: string
  editorial_summary?: { overview?: string }
}

type EnrichedRestaurant = Restaurant & {
  placeDetails?: PlaceDetails
  photoUrl?: string
  enriched?: boolean
}

const CUISINE_FILTERS = [
  "All", "American", "Italian", "Mexican", "Chinese", "Japanese",
  "Indian", "Thai", "Mediterranean", "Pizza", "Burgers", "Seafood",
  "Vegan", "Breakfast", "Desserts", "Bars",
]

const PRICE_FILTERS = [
  { label: "All", value: null },
  { label: "$", value: 0 },
  { label: "$$", value: 1 },
  { label: "$$$", value: 2 },
  { label: "$$$$", value: 3 },
]

async function fetchPlaceDetails(name: string): Promise<PlaceDetails | null> {
  try {
    const params = new URLSearchParams({ query: name, limit: "1", opennow: "false" })
    const res = await fetch(`${dbUrl}/places/search?${params}`)
    if (!res.ok) return null
    const data = await res.json()
    return data.results?.[0] ?? null
  } catch {
    return null
  }
}

function getPhotoUrl(place: PlaceDetails): string | null {
  const ref = place.photos?.[0]?.photo_reference
  if (!ref) return null
  return `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference=${ref}&key=${process.env.NEXT_PUBLIC_GOOGLE_API_KEY}`
}

const PriceLevel = ({ level }: { level?: number }) => {
  if (level == null) return null
  return (
    <span style={{ color: "#16a34a", fontWeight: 600, fontSize: 13 }}>
      {"$".repeat(level + 1)}
      <span style={{ color: "#d1d5db" }}>{"$".repeat(Math.max(0, 3 - level))}</span>
    </span>
  )
}

const StarRating = ({ rating, total }: { rating?: number; total?: number }) => {
  if (!rating) return null
  const full = Math.round(rating)
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <span style={{ color: "#f59e0b", fontSize: 13 }}>{"★".repeat(full)}{"☆".repeat(5 - full)}</span>
      <span style={{ color: "#6b7280", fontSize: 12 }}>{rating.toFixed(1)}{total ? ` (${total.toLocaleString()})` : ""}</span>
    </div>
  )
}

function RestaurantPopover({ restaurant, onClose, onMarkInterested }: {
  restaurant: EnrichedRestaurant
  onClose: () => void
  onMarkInterested: (r: EnrichedRestaurant) => void
}) {
  const place = restaurant.placeDetails
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose() }
    document.addEventListener("keydown", handler)
    return () => document.removeEventListener("keydown", handler)
  }, [onClose])

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,0,0,0.55)", backdropFilter: "blur(4px)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#fff", borderRadius: 16, width: "100%", maxWidth: 620, maxHeight: "88vh", overflowY: "auto", boxShadow: "0 24px 64px rgba(0,0,0,0.25)" }}>
        <div style={{ position: "relative", width: "100%", height: 220, background: "#f3f4f6", borderRadius: "16px 16px 0 0", overflow: "hidden" }}>
          {restaurant.photoUrl
            ? <img src={restaurant.photoUrl} alt={restaurant.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            : <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", fontSize: 48 }}>🍽️</div>
          }
          <button onClick={onClose} style={{ position: "absolute", top: 12, right: 12, width: 32, height: 32, borderRadius: "50%", border: "none", background: "rgba(0,0,0,0.5)", color: "#fff", cursor: "pointer", fontSize: 20, lineHeight: "32px", textAlign: "center" }}>×</button>
          {place?.opening_hours?.open_now != null && (
            <span style={{ position: "absolute", bottom: 12, left: 12, background: place.opening_hours.open_now ? "#16a34a" : "#dc2626", color: "#fff", padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 600 }}>
              {place.opening_hours.open_now ? "Open now" : "Closed"}
            </span>
          )}
        </div>
        <div style={{ padding: "20px 24px 28px" }}>
          <h2 style={{ margin: "0 0 8px", fontSize: 22, color: "#111827", fontWeight: 700 }}>{restaurant.name}</h2>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 10 }}>
            <StarRating rating={place?.rating} total={place?.user_ratings_total} />
            <PriceLevel level={place?.price_level} />
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
            {restaurant.categories.slice(0, 5).map(cat => (
              <span key={cat} style={{ background: "#f3f4f6", color: "#374151", padding: "3px 10px", borderRadius: 20, fontSize: 12, fontWeight: 500 }}>{cat}</span>
            ))}
          </div>
          {place?.editorial_summary?.overview && <p style={{ color: "#4b5563", fontSize: 14, lineHeight: 1.6, margin: "0 0 16px" }}>{place.editorial_summary.overview}</p>}
          {restaurant.reason && <p style={{ color: "#6b7280", fontSize: 13, fontStyle: "italic", margin: "0 0 16px" }}>{restaurant.reason}</p>}
          {place?.formatted_address && <div style={{ display: "flex", gap: 8, alignItems: "flex-start", marginBottom: 10 }}><span>📍</span><span style={{ color: "#4b5563", fontSize: 14 }}>{place.formatted_address}</span></div>}
          {place?.phone_number && <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10 }}><span>📞</span><a href={`tel:${place.phone_number}`} style={{ color: "#3b82f6", fontSize: 14, textDecoration: "none" }}>{place.phone_number}</a></div>}
          {place?.website && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10 }}>
              <span>🌐</span>
              <a href={place.website} target="_blank" rel="noopener noreferrer" style={{ color: "#3b82f6", fontSize: 14, textDecoration: "none", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 400 }}>
                {place.website.replace(/^https?:\/\//, "")}
              </a>
            </div>
          )}
          {place?.opening_hours?.weekday_text && place.opening_hours.weekday_text.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h4 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600, color: "#111827" }}>Hours</h4>
              <div style={{ background: "#f9fafb", borderRadius: 8, padding: "10px 14px" }}>
                {place.opening_hours.weekday_text.map((line, i) => <div key={i} style={{ fontSize: 13, color: "#4b5563", lineHeight: 1.8 }}>{line}</div>)}
              </div>
            </div>
          )}
          {place?.reviews && place.reviews.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h4 style={{ margin: "0 0 10px", fontSize: 14, fontWeight: 600, color: "#111827" }}>Reviews</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {place.reviews.slice(0, 3).map((r, i) => (
                  <div key={i} style={{ background: "#f9fafb", borderRadius: 8, padding: "10px 14px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{r.author_name}</span>
                      <span style={{ color: "#f59e0b", fontSize: 13 }}>{"★".repeat(r.rating)}</span>
                    </div>
                    <p style={{ margin: "0 0 4px", fontSize: 13, color: "#4b5563", lineHeight: 1.5 }}>{r.text.length > 200 ? r.text.slice(0, 200) + "…" : r.text}</p>
                    <span style={{ fontSize: 11, color: "#9ca3af" }}>{r.relative_time_description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
            {place?.google_maps_url && (
              <a href={place.google_maps_url} target="_blank" rel="noopener noreferrer" style={{ flex: 1, padding: "11px 0", background: "#3b82f6", color: "#fff", borderRadius: 8, textAlign: "center", textDecoration: "none", fontSize: 14, fontWeight: 600 }}>Open in Maps</a>
            )}
            <button onClick={() => { onMarkInterested(restaurant); onClose() }} style={{ flex: 1, padding: "11px 0", background: "#f3f4f6", color: "#374151", border: "none", borderRadius: 8, cursor: "pointer", fontSize: 14, fontWeight: 600 }}>✓ Interested</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function RestaurantCard({ restaurant, onClick }: { restaurant: EnrichedRestaurant; onClick: () => void }) {
  const hash = restaurant.business_id.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0)
  return (
    <article onClick={onClick} style={{ background: "#fff", borderRadius: 12, overflow: "hidden", cursor: "pointer", boxShadow: "0 2px 10px rgba(0,0,0,0.07)", transition: "transform 0.15s, box-shadow 0.15s" }}
      onMouseEnter={e => { const el = e.currentTarget as HTMLElement; el.style.transform = "translateY(-3px)"; el.style.boxShadow = "0 8px 24px rgba(0,0,0,0.12)" }}
      onMouseLeave={e => { const el = e.currentTarget as HTMLElement; el.style.transform = "translateY(0)"; el.style.boxShadow = "0 2px 10px rgba(0,0,0,0.07)" }}
    >
      <div style={{ position: "relative", width: "100%", height: 170, background: `hsl(${hash % 360}, 55%, 93%)`, overflow: "hidden" }}>
        {restaurant.photoUrl
          ? <img src={restaurant.photoUrl} alt={restaurant.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          : !restaurant.enriched
            ? <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#9ca3af", fontSize: 12 }}>Loading...</div>
            : <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", fontSize: 32 }}>🍽️</div>
        }
        {restaurant.placeDetails?.rating && (
          <span style={{ position: "absolute", top: 8, right: 8, background: "rgba(0,0,0,0.65)", color: "#f59e0b", padding: "3px 8px", borderRadius: 20, fontSize: 12, fontWeight: 700 }}>
            ★ {restaurant.placeDetails.rating.toFixed(1)}
          </span>
        )}
        {restaurant.placeDetails?.opening_hours?.open_now != null && (
          <span style={{ position: "absolute", top: 8, left: 8, background: restaurant.placeDetails.opening_hours.open_now ? "#16a34a" : "#dc2626", color: "#fff", padding: "3px 8px", borderRadius: 20, fontSize: 11, fontWeight: 600 }}>
            {restaurant.placeDetails.opening_hours.open_now ? "Open" : "Closed"}
          </span>
        )}
        {restaurant.score != null && (
          <span style={{ position: "absolute", bottom: 8, right: 8, background: "rgba(59,130,246,0.88)", color: "#fff", padding: "3px 8px", borderRadius: 20, fontSize: 11, fontWeight: 600 }}>
            {(restaurant.score * 100).toFixed(0)}% match
          </span>
        )}
      </div>
      <div style={{ padding: "12px 14px" }}>
        <h3 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 600, color: "#111827", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{restaurant.name}</h3>
        <p style={{ margin: "0 0 8px", fontSize: 12, color: "#6b7280", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{restaurant.categories.slice(0, 3).join(" · ")}</p>
        <PriceLevel level={restaurant.placeDetails?.price_level} />
      </div>
    </article>
  )
}

export default function Home() {
  const router = useRouter()
  const [feed, setFeed] = useState<EnrichedRestaurant[]>([])
  const [feedLabel, setFeedLabel] = useState<"recommendations" | "random">("random")
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<EnrichedRestaurant | null>(null)
  const [cuisineFilter, setCuisineFilter] = useState("All")
  const [priceFilter, setPriceFilter] = useState<number | null>(null)
  const [userCity, setUserCity] = useState<string | null>(null)
  const enrichCache = useRef<Record<string, PlaceDetails | null>>({})

  useEffect(() => {
    if (!isAuthenticated()) { router.push("/"); return }
    fetchFeed()
    // Fetch city from tracking endpoint
    authenticatedFetch(`${dbUrl}/tracking/current-city`)
      .then(r => r.json())
      .then(d => { if (d.city) setUserCity(d.city) })
      .catch(() => {})
  }, [router])

  const enrichRestaurant = useCallback(async (r: Restaurant): Promise<EnrichedRestaurant> => {
    let place: PlaceDetails | null
    if (r.name in enrichCache.current) {
      place = enrichCache.current[r.name]
    } else {
      place = await fetchPlaceDetails(r.name)
      enrichCache.current[r.name] = place
    }
    const photoUrl = place ? (getPhotoUrl(place) ?? undefined) : undefined
    return { ...r, placeDetails: place ?? undefined, photoUrl, enriched: true }
  }, [])

  const enrichList = useCallback((raw: EnrichedRestaurant[], setter: React.Dispatch<React.SetStateAction<EnrichedRestaurant[]>>) => {
    raw.forEach(async (r, i) => {
      const enriched = await enrichRestaurant(r)
      setter(prev => prev.map((p, pi) => pi === i ? enriched : p))
    })
  }, [enrichRestaurant])

  const fetchFeed = async () => {
    setLoading(true)
    try {
      const recData = await getTop20Recommendations().catch(() => ({ success: false, recommendations: [], user_click_count: 0 }))
      if (recData.success && recData.user_click_count > 0 && recData.recommendations?.length > 0) {
        setFeedLabel("recommendations")
        const raw: EnrichedRestaurant[] = recData.recommendations.map((r: Restaurant) => ({ ...r, enriched: false }))
        setFeed(raw)
        enrichList(raw, setFeed)
      } else {
        setFeedLabel("random")
        const randomData = await getRandomRestaurants(10).catch(() => ({ success: false, restaurants: [] }))
        if (randomData.success) {
          const raw: EnrichedRestaurant[] = (randomData.restaurants || []).map((r: Restaurant) => ({ ...r, enriched: false }))
          setFeed(raw)
          enrichList(raw, setFeed)
        }
      }
    } catch (err) {
      console.error("Error fetching feed:", err)
    } finally {
      setLoading(false)
    }
  }

  // Client-side filtering
  const filteredFeed = feed.filter(r => {
    const matchesCuisine = cuisineFilter === "All" ||
      r.categories.some(cat => cat.toLowerCase().includes(cuisineFilter.toLowerCase()))
    const matchesPrice = priceFilter === null ||
      r.placeDetails?.price_level === priceFilter
    return matchesCuisine && matchesPrice
  })

  const handleCardClick = async (restaurant: EnrichedRestaurant) => {
    recordClick(restaurant.business_id).catch(console.error)
    setSelected(restaurant)
  }

  if (loading) {
    return (
      <SideNavbar>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
          <div style={{ fontSize: 18, color: "#6b7280" }}>Loading restaurants...</div>
        </div>
      </SideNavbar>
    )
  }

  return (
    <SideNavbar>
      <div style={{ padding: "20px", width: "100%", boxSizing: "border-box" }}>

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, background: "#fff", padding: "16px 20px", borderRadius: 12, boxShadow: "0 2px 8px rgba(0,0,0,0.07)" }}>
          <div>
            <h1 style={{ margin: "0 0 4px", fontSize: 20, color: "#111827", fontWeight: 700 }}>🍽️ Food Recommendations</h1>
            <p style={{ margin: 0, fontSize: 13, color: "#6b7280" }}>
              {feedLabel === "recommendations" ? "Personalized picks based on your taste" : "Discover something new — swipe on restaurants to personalize your feed"}
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {userCity && (
              <span style={{ fontSize: 13, color: "#6b7280", display: "flex", alignItems: "center", gap: 4 }}>
                📍 Irvine
              </span>
            )}
            <button onClick={() => { removeToken(); router.push("/") }} style={{ padding: "8px 16px", background: "#fee2e2", color: "#dc2626", border: "none", borderRadius: 8, cursor: "pointer", fontSize: 14, fontWeight: 600 }}>Logout</button>
          </div>
        </div>

        {/* Filters */}
        <div style={{ background: "#fff", borderRadius: 12, padding: "14px 16px", marginBottom: 16, boxShadow: "0 2px 8px rgba(0,0,0,0.07)" }}>
          <div style={{ marginBottom: 12 }}>
            <p style={{ margin: "0 0 8px", fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em" }}>Cuisine</p>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {CUISINE_FILTERS.map(c => (
                <button key={c} onClick={() => setCuisineFilter(c)} style={{
                  padding: "5px 12px", borderRadius: 20, fontSize: 13, fontWeight: 500, cursor: "pointer",
                  border: cuisineFilter === c ? "none" : "1px solid #e5e7eb",
                  background: cuisineFilter === c ? "#111827" : "#fff",
                  color: cuisineFilter === c ? "#fff" : "#374151",
                  transition: "all 0.15s",
                }}>{c}</button>
              ))}
            </div>
          </div>
          <div>
            <p style={{ margin: "0 0 8px", fontSize: 11, fontWeight: 600, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.06em" }}>Price range</p>
            <div style={{ display: "flex", gap: 6 }}>
              {PRICE_FILTERS.map(p => (
                <button key={p.label} onClick={() => setPriceFilter(p.value)} style={{
                  padding: "5px 16px", borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: "pointer",
                  border: priceFilter === p.value ? "none" : "1px solid #e5e7eb",
                  background: priceFilter === p.value ? "#111827" : "#fff",
                  color: priceFilter === p.value ? "#fff" : "#374151",
                  transition: "all 0.15s",
                }}>{p.label}</button>
              ))}
            </div>
          </div>
        </div>

        {/* Feed label + count */}
        <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            background: feedLabel === "recommendations" ? "#eff6ff" : "#f3f4f6",
            color: feedLabel === "recommendations" ? "#1d4ed8" : "#6b7280",
            padding: "5px 14px", borderRadius: 20, fontSize: 13, fontWeight: 600,
          }}>
            {feedLabel === "recommendations" ? "⭐ Personalized for you" : "🎲 Explore & discover"}
          </span>
          <span style={{ color: "#9ca3af", fontSize: 13 }}>
            {filteredFeed.length} restaurant{filteredFeed.length !== 1 ? "s" : ""}
            {filteredFeed.length !== feed.length ? ` (filtered from ${feed.length})` : ""}
          </span>
        </div>

        {/* Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 18 }}>
          {filteredFeed.length > 0 ? filteredFeed.map((r, i) => (
            <RestaurantCard key={r.business_id + i} restaurant={r} onClick={() => handleCardClick(r)} />
          )) : (
            <div style={{ textAlign: "center", padding: 48, color: "#6b7280", background: "#fff", borderRadius: 12 }}>
              {feed.length > 0 ? "No restaurants match your filters — try adjusting them" : "No restaurants available"}
            </div>
          )}
        </div>
      </div>

      {selected && (
        <RestaurantPopover
          restaurant={selected}
          onClose={() => setSelected(null)}
          onMarkInterested={(r) => console.log(`Marked interested: ${r.name}`)}
        />
      )}
    </SideNavbar>
  )
}