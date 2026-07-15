import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/auth-context';
import { ToastProvider } from '@/components/Toast';
import { Navbar } from '@/components/Navbar';
import { LayoutShell } from '@/components/LayoutShell';

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
      <body className={`${inter.className} bg-gray-950 text-gray-100`}>
        <AuthProvider>
          <ToastProvider>
            <Navbar />
            <LayoutShell>{children}</LayoutShell>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
