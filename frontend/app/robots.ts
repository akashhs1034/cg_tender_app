import type { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        // No value in indexing auth flows, admin, or API endpoints.
        disallow: ['/admin', '/api/', '/login', '/signup', '/forgot-password', '/reset-password', '/auth/'],
      },
    ],
    sitemap: 'https://opporta.vercel.app/sitemap.xml',
  }
}
