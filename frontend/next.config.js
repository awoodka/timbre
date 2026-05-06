/** @type {import('next').NextConfig} */
const API_TARGET = process.env.API_TARGET || 'http://localhost:8000'

const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'covers.openlibrary.org' },
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
