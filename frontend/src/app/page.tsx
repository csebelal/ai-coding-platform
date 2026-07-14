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
    <div className="max-w-7xl mx-auto py-12 sm:px-6 lg:px-8">
      <div className="px-4 py-12 sm:px-0">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI Coding Platform
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Multi-agent AI software engineering platform. 
            Plan, code, test, and review — all orchestrated by AI.
          </p>
          <div className="space-x-4">
            <button
              onClick={() => router.push('/login')}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              Get Started
            </button>
            <button
              onClick={() => router.push('/login')}
              className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Sign In
            </button>
          </div>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-primary-600 text-2xl font-bold mb-2">Plan</div>
            <p className="text-gray-600">AI analyzes your task and creates a detailed implementation plan with file-level specificity.</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-primary-600 text-2xl font-bold mb-2">Code</div>
            <p className="text-gray-600">Specialized agents write tests, implement code, review quality, and generate documentation.</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-primary-600 text-2xl font-bold mb-2">Verify</div>
            <p className="text-gray-600">Automated verification with a debugging loop that fixes issues until the code passes all checks.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
