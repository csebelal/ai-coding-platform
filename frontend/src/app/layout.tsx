import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/auth-context';
import { ToastProvider } from '@/components/Toast';
import { Navbar } from '@/components/Navbar';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI Coding Platform',
  description: 'AI Software Engineering Platform with multi-agent orchestration',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <ToastProvider>
            <div className="min-h-screen bg-gray-50">
              <Navbar />
              <main>{children}</main>
            </div>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
