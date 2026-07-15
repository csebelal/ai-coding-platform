'use client';

import { usePathname } from 'next/navigation';

export function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublicPage = pathname === '/login' || pathname === '/';

  if (isPublicPage) {
    return <main>{children}</main>;
  }

  return (
    <div className="lg:ml-64 min-h-screen bg-gray-950">
      <nav className="bg-gray-900 border-b border-gray-800 h-12 flex items-center px-4 lg:px-6 sticky top-0 z-20">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">AI Coding Platform</span>
          <span className="text-xs text-gray-600">/</span>
          <span className="text-xs text-gray-400 capitalize">{pathname.split('/')[1] || 'dashboard'}</span>
        </div>
      </nav>
      <main className="min-h-[calc(100vh-48px)]">{children}</main>
    </div>
  );
}
