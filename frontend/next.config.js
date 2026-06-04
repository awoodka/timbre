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
      // Film/TV posters from TMDB.
      { protocol: 'https', hostname: 'image.tmdb.org' },
      // Anime/manga covers from MyAnimeList (Jikan).
      { protocol: 'https', hostname: 'cdn.myanimelist.net' },
      // Video game covers from RAWG.
      { protocol: 'https', hostname: 'media.rawg.io' },
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
