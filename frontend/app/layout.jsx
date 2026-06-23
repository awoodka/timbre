import { Inter } from 'next/font/google'
import Link from 'next/link'
import { AuthProvider } from '@/lib/auth-context'
import { RatingsProvider } from '@/lib/ratings-context'
import { SavesProvider } from '@/lib/saves-context'
import NavLinks from '@/components/NavLinks'
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
        <AuthProvider>
          <RatingsProvider>
            <SavesProvider>
              <div className="app">
                <nav className="navbar">
                  <Link href="/" className="nav-logo">Timbre</Link>
                  <NavLinks />
                </nav>
                <main className="main-content">{children}</main>
              </div>
            </SavesProvider>
          </RatingsProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
