import { Inter } from 'next/font/google'
import Link from 'next/link'
import { AuthProvider } from '@/lib/auth-context'
import { ThemeProvider } from '@/lib/theme-context'
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

// Runs before first paint (no React, no deps): set <html data-theme> from the stored
// preference so dark-mode users never see a light flash. Mirrors theme-context.jsx.
const THEME_INIT = `(function(){try{var t=localStorage.getItem('timbre.theme')||'system';var d=t==='dark'||(t==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.setAttribute('data-theme',d?'dark':'light');}catch(e){}})();`

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT }} />
        <AuthProvider>
          <ThemeProvider>
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
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
