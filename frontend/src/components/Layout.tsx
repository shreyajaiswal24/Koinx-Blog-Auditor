import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { clearToken, clearStoredUser, getStoredUser } from '../api/client';

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/findings', label: 'Findings' },
  { to: '/live', label: 'Live Audit' },
  { to: '/audits', label: 'Audits' },
];

export default function Layout() {
  const navigate = useNavigate();
  const user = getStoredUser();

  const handleLogout = () => {
    clearToken();
    clearStoredUser();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 text-gray-300 flex flex-col shrink-0">
        <div className="px-5 py-5 text-white font-bold text-lg border-b border-gray-700">
          KoinX Tax Auditor
        </div>
        <nav className="flex-1 py-4 space-y-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `block px-5 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-gray-800 text-white border-l-4 border-blue-500'
                    : 'hover:bg-gray-800 hover:text-white border-l-4 border-transparent'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        {/* User info + Logout */}
        <div className="border-t border-gray-700 px-5 py-4">
          {user && (
            <div className="text-sm text-gray-400 mb-2 truncate">{user.name}</div>
          )}
          <button
            onClick={handleLogout}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
