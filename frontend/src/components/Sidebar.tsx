'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/accounts', label: 'Accounts', icon: '🔗' },
  { href: '/posts', label: 'Posts', icon: '📝' },
  { href: '/content', label: 'Content', icon: '💡' },
  { href: '/analytics', label: 'Analytics', icon: '📈' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-primary-600">SocialAI</h1>
        <p className="text-sm text-gray-500 mt-1">Content Manager</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              pathname === item.href
                ? 'bg-primary-50 text-primary-700'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <span>{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 px-4 py-2">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-medium text-sm">
            {user?.display_name?.[0] || user?.email?.[0] || '?'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.display_name || user?.email}</p>
            <p className="text-xs text-gray-500 capitalize">{user?.plan_tier} plan</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full mt-2 px-4 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors text-left"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
