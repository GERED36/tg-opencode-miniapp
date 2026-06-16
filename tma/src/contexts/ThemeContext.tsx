import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { getTelegramTheme, ready } from '../services/tgApi'
import type { TelegramTheme } from '../types'

const defaultTheme: TelegramTheme = {
  bgColor: '#0d1117',
  textColor: '#e6edf3',
  hintColor: '#8b949e',
  linkColor: '#58a6ff',
  buttonColor: '#3fb950',
  buttonTextColor: '#ffffff',
  secondaryBgColor: '#161b22',
  colorScheme: 'dark',
}

const ThemeContext = createContext<TelegramTheme>(defaultTheme)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<TelegramTheme>(defaultTheme)

  useEffect(() => {
    ready()
    setTheme(getTelegramTheme())

    const tg = window.Telegram?.WebApp
    if (tg) {
      tg.onEvent('themeChanged', () => {
        setTheme(getTelegramTheme())
      })
    }
  }, [])

  return (
    <ThemeContext.Provider value={theme}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): TelegramTheme {
  return useContext(ThemeContext)
}
