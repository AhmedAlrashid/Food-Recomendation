'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated, removeToken } from '../api_call/authUtils'

interface ProtectedRouteProps {
  children: React.ReactNode
  showLogout?: boolean
}

export default function ProtectedRoute({ children, showLogout = true }: ProtectedRouteProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/') // Redirect to login page
      return
    }
    setLoading(false)
  }, [router])

  const handleLogout = () => {
    removeToken()
    router.push('/')
  }

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px'
      }}>
        Checking authentication...
      </div>
    )
  }

  return (
    <>
      {showLogout && (
        <button 
          onClick={handleLogout}
          style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            zIndex: 1000,
            padding: '10px 20px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }}
        >
          Logout
        </button>
      )}
      {children}
    </>
  )
}