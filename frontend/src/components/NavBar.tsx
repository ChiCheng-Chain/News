import { Link, useLocation } from 'react-router-dom'

export function NavBar() {
  const { pathname } = useLocation()
  const links = [
    { to: '/', label: '每日简报' },
    { to: '/topics', label: '主题聚合' },
    { to: '/sources', label: '来源管理' },
  ]
  return (
    <nav className="bg-gray-900 text-white px-6 py-3 flex items-center gap-8">
      <span className="font-bold text-lg">🌐 打破信息茧房</span>
      <div className="flex gap-6">
        {links.map(l => (
          <Link
            key={l.to}
            to={l.to}
            className={`text-sm hover:text-blue-300 transition-colors ${
              pathname === l.to ? 'text-blue-400 font-medium' : 'text-gray-300'
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
