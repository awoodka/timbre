/** @type {import('next').NextConfig} */
const API_TARGET = process.env.API_TARGET || 'http://localhost:8000'

const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      // Existing seeded covers come from Open Library...
      { protocol: 'https', hostname: 'covers.openlibrary.org' },
      // ...newly analyzed books get covers from the Google Books API.
      { protocol: 'https', hostname: 'books.google.com' },
      { protocol: 'https', hostname: 'books.googleusercontent.com' },
      // Film posters from TMDB.
      { protocol: 'https', hostname: 'image.tmdb.org' },
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_TARGET}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
