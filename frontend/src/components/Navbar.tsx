'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter, usePathname } from 'next/navigation';
import { useState } from 'react';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/workflow', label: 'Workflow', icon: '⚡' },
  { path: '/projects', label: 'Projects', icon: '📁' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

export function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isAuthPage = pathname === '/login';

  if (isAuthPage || !isAuthenticated) {
    return (
      <nav className="bg-gray-900 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-14 items-center">
            <button onClick={() => router.push('/')} className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs text-white font-bold">AI</span>
              AI Coding Platform
            </button>
            {isAuthenticated && (
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-400">{user?.email}</span>
                <button onClick={() => { logout(); router.push('/login'); }} className="text-sm text-gray-400 hover:text-white transition-colors">Logout</button>
              </div>
            )}
          </div>
        </div>
      </nav>
    );
  }

  return (
    <>
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-3 left-3 z-50 w-9 h-9 bg-gray-800 rounded-lg flex items-center justify-center text-white border border-gray-700"
      >
        {mobileOpen ? '✕' : '☰'}
      </button>

      <aside className={`fixed top-0 left-0 h-full w-64 bg-gray-900 border-r border-gray-800 z-40 transform transition-transform duration-200 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}>
        <div className="flex items-center gap-2 h-14 px-5 border-b border-gray-800">
          <span className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs text-white font-bold">AI</span>
          <span className="text-sm font-bold text-white">AI Platform</span>
        </div>

        <nav className="p-3 space-y-1">
          {NAV_ITEMS.map(item => (
            <button
              key={item.path}
              onClick={() => { router.push(item.path); setMobileOpen(false); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                pathname === item.path || pathname.startsWith(item.path + '/')
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-800/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 border border-transparent'
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-gray-800">
          <div className="px-3 py-2.5 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs text-white font-bold">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-200 truncate">{user?.full_name || user?.email}</div>
              <div className="text-xs text-gray-500 truncate">{user?.email}</div>
            </div>
            <button
              onClick={() => { logout(); router.push('/login'); }}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
              title="Logout"
            >
              ↪
            </button>
          </div>
        </div>
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={() => setMobileOpen(false)} />
      )}
    </>
  );
}
