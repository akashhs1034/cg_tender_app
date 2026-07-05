import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Opporta — Government Tenders & Jobs (CG & UP)',
    short_name: 'Opporta',
    description:
      'Live government tenders, jobs and recruitment notices for Chhattisgarh & Uttar Pradesh, with AI eligibility and bid help.',
    start_url: '/dashboard',
    scope: '/',
    display: 'standalone',
    orientation: 'portrait',
    background_color: '#080E1D',
    theme_color: '#0D1525',
    lang: 'en',
    categories: ['business', 'productivity', 'government'],
    icons: [
      { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      { src: '/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
    shortcuts: [
      { name: 'Tenders', url: '/tenders' },
      { name: 'Jobs', url: '/jobs' },
      { name: 'Exam Planner', url: '/exam-planner' },
    ],
  }
}
