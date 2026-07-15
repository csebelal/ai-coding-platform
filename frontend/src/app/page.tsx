'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-7xl mx-auto px-4 py-20">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl text-white font-bold mx-auto mb-6">
            AI
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">
            AI Coding Platform
          </h1>
          <p className="text-lg text-gray-400 mb-10 max-w-2xl mx-auto">
            Multi-agent AI software engineering platform. 
            Plan, code, test, and review — all orchestrated by AI.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => router.push('/login')}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl text-base font-medium transition-all"
            >
              Get Started
            </button>
            <button
              onClick={() => router.push('/login')}
              className="px-6 py-3 bg-gray-800 border border-gray-700 hover:bg-gray-700 text-gray-300 rounded-xl text-base font-medium transition-all"
            >
              Sign In
            </button>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-1 gap-6 md:grid-cols-3">
          {[
            { icon: '📋', title: 'Plan', desc: 'AI analyzes your task and creates a detailed implementation plan.' },
            { icon: '💻', title: 'Code', desc: 'Specialized agents write tests, implement code, and review quality.' },
            { icon: '✅', title: 'Verify', desc: 'Automated verification with a debugging loop for perfect code.' },
          ].map(f => (
            <div key={f.title} className="bg-gray-900 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-all">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-gray-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
