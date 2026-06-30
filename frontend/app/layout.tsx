import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Inter, Plus_Jakarta_Sans, Geist_Mono, Orbitron } from 'next/font/google'
import { LanguageProvider } from '@/lib/language-context'
import { ToastProvider } from '@/components/ui/toast'
import './globals.css'

const inter = Inter({ variable: '--font-inter', subsets: ['latin'] })
const plusJakarta = Plus_Jakarta_Sans({
  variable: '--font-plus-jakarta',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
})
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] })
const orbitron = Orbitron({
  variable: '--font-orbitron',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800', '900'],
})

export const metadata: Metadata = {
  title: 'OPPORTA — Opportunity Intelligence Platform',
  description:
    'Track tenders, jobs, notices, contracts, corrigendums, and upcoming opportunities across your target markets.',
  generator: 'v0.app',
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#080E1D',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${plusJakarta.variable} ${geistMono.variable} ${orbitron.variable} bg-background`}
    >
      <body className="font-sans antialiased min-h-screen">
        <LanguageProvider>
          <ToastProvider>
            {children}
          </ToastProvider>
        </LanguageProvider>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
