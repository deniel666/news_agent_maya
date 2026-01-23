import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  CheckCircle,
  BarChart3,
  Settings,
  Tv,
} from 'lucide-react'
import { cn } from '../lib/utils'

interface LayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Briefings', href: '/briefings', icon: FileText },
  { name: 'Approvals', href: '/approvals', icon: CheckCircle },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-card border-r border-dark-border flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-dark-border">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-maya-500 to-maya-700 rounded-xl flex items-center justify-center">
              <Tv className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Maya</h1>
              <p className="text-xs text-gray-400">AI News Anchor</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href ||
                (item.href !== '/' && location.pathname.startsWith(item.href))

              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={cn(
                      'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                      isActive
                        ? 'bg-maya-600 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-dark-border'
                    )}
                  >
                    <item.icon className="w-5 h-5" />
                    {item.name}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-dark-border">
          <div className="text-xs text-gray-500">
            <p>Maya AI News Anchor</p>
            <p>Version 1.0.0</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
