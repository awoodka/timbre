import { Inter } from 'next/font/google'
import Link from 'next/link'
import { RatingsProvider } from '@/lib/ratings-context'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata = {
  title: 'Timbre',
  description: 'Emotional book recommendation engine',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <RatingsProvider>
          <div className="app">
            <nav className="navbar">
              <Link href="/" className="nav-logo">Timbre</Link>
              <div className="nav-links">
                <Link href="/">Home</Link>
                <Link href="/library">Library</Link>
              </div>
            </nav>
            <main className="main-content">{children}</main>
          </div>
        </RatingsProvider>
      </body>
    </html>
  )
}
