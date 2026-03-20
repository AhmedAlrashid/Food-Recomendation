import React from 'react'
import { useRouter, usePathname } from 'next/navigation'

type SideNavbarProps = {
  children: React.ReactNode
}

const SideNavbar = ({ children }: SideNavbarProps) => {
  const router = useRouter()
  const pathname = usePathname()

  const navItems = [
    { name: 'Home', path: '/home', icon: '🏠' },
    { name: 'Swipes', path: '/swipe', icon: '👆' },
  ]

  const sidebarStyle: React.CSSProperties = {
    position: 'fixed',
    left: 0,
    top: 0,
    width: 200,
    height: '100vh',
    backgroundColor: '#1f2937',
    color: 'white',
    display: 'flex',
    flexDirection: 'column',
    zIndex: 1000,
  }

  const logoStyle: React.CSSProperties = {
    padding: '20px',
    borderBottom: '1px solid #374151',
    fontSize: '18px',
    fontWeight: 'bold',
    textAlign: 'center',
  }

  const navStyle: React.CSSProperties = {
    flex: 1,
    paddingTop: '20px',
  }

  const navItemStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 20px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    fontSize: '14px',
    gap: '12px',
  }

  const activeNavItemStyle: React.CSSProperties = {
    ...navItemStyle,
    backgroundColor: '#3b82f6',
  }

  const hoverNavItemStyle: React.CSSProperties = {
    ...navItemStyle,
    backgroundColor: '#374151',
  }

  const mainContentStyle: React.CSSProperties = {
    marginLeft: 200,
    minHeight: '100vh',
    width: 'calc(100vw - 200px)',
    backgroundColor: '#f9fafb',
  }

  return (
    <div style={{ display: 'flex' }}>
      <div style={sidebarStyle}>
        <div style={logoStyle}>
          🍽️ FoodRec
        </div>
        <nav style={navStyle}>
          {navItems.map((item) => {
            const isActive = pathname === item.path
            return (
              <div
                key={item.path}
                style={isActive ? activeNavItemStyle : navItemStyle}
                onClick={() => router.push(item.path)}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = '#374151'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }
                }}
              >
                <span style={{ fontSize: '16px' }}>{item.icon}</span>
                <span>{item.name}</span>
              </div>
            )
          })}
        </nav>
      </div>
      <main style={mainContentStyle}>
        {children}
      </main>
    </div>
  )
}

export default SideNavbar