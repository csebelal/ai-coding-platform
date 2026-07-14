'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';

export function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const router = useRouter();

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-8">
            <button
              onClick={() => router.push('/')}
              className="text-xl font-bold text-primary-600"
            >
              AI Coding Platform
            </button>
            {isAuthenticated && (
              <>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="text-gray-700 hover:text-primary-600 text-sm font-medium"
                >
                  Dashboard
                </button>
                <button
                  onClick={() => router.push('/projects')}
                  className="text-gray-700 hover:text-primary-600 text-sm font-medium"
                >
                  Projects
                </button>
                <button
                  onClick={() => router.push('/settings')}
                  className="text-gray-700 hover:text-primary-600 text-sm font-medium"
                >
                  Settings
                </button>
              </>
            )}
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <span className="text-sm text-gray-600">{user?.email}</span>
                <button
                  onClick={() => { logout(); router.push('/login'); }}
                  className="text-sm text-gray-700 hover:text-primary-600"
                >
                  Logout
                </button>
              </>
            ) : (
              <button
                onClick={() => router.push('/login')}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm font-medium"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
