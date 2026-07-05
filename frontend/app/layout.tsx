import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Inter, Plus_Jakarta_Sans, Geist_Mono, Orbitron } from 'next/font/google'
import { LanguageProvider } from '@/lib/language-context'
import { AuthProvider } from '@/lib/auth-context'
import { SavedProvider } from '@/lib/saved-context'
import { SavedJobsProvider } from '@/lib/saved-jobs-context'
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
  metadataBase: new URL('https://opporta.vercel.app'),
  title: {
    default: 'Opporta — Government Tenders & Jobs for Chhattisgarh & UP',
    template: '%s | Opporta',
  },
  description:
    'Live government tenders, jobs, and recruitment notices for Chhattisgarh and Uttar Pradesh — e-Procurement, GeM, PSU, PSC/Vyapam/UPSSSC and more, with AI eligibility and bid help.',
  keywords: [
    'Chhattisgarh tenders', 'Uttar Pradesh tenders', 'government tenders',
    'GeM bids', 'CG e-procurement', 'sarkari naukri', 'CGPSC', 'UPPSC', 'Vyapam',
    'government jobs', 'e-tender', 'CSPDCL tender',
  ],
  openGraph: {
    title: 'Opporta — Government Tenders & Jobs (CG & UP)',
    description:
      'Live government tenders and jobs for Chhattisgarh & Uttar Pradesh, with AI eligibility and bid drafting.',
    url: 'https://opporta.vercel.app',
    siteName: 'Opporta',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Opporta — Government Tenders & Jobs (CG & UP)',
    description: 'Live CG & UP government tenders and jobs, with AI eligibility and bid help.',
  },
  manifest: '/manifest.webmanifest',
  applicationName: 'Opporta',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'Opporta',
  },
  icons: {
    icon: [
      { url: '/favicon-32.png', sizes: '32x32', type: 'image/png' },
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
    ],
    apple: [{ url: '/apple-icon.png', sizes: '180x180', type: 'image/png' }],
  },
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#0D1525',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
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
        <AuthProvider>
          <LanguageProvider>
            <ToastProvider>
              <SavedProvider>
                <SavedJobsProvider>
                  {children}
                </SavedJobsProvider>
              </SavedProvider>
            </ToastProvider>
          </LanguageProvider>
        </AuthProvider>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
