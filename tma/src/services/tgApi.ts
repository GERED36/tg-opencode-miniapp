import type { TelegramTheme } from '../types'

export function getTelegramWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null
}

export function getInitData(): string {
  const tg = getTelegramWebApp()
  return tg?.initData ?? ''
}

export function getTelegramTheme(): TelegramTheme {
  const tg = getTelegramWebApp()
  const tp = tg?.themeParams ?? {}
  return {
    bgColor: tp.bg_color ?? '#0d1117',
    textColor: tp.text_color ?? '#e6edf3',
    hintColor: tp.hint_color ?? '#8b949e',
    linkColor: tp.link_color ?? '#58a6ff',
    buttonColor: tp.button_color ?? '#3fb950',
    buttonTextColor: tp.button_text_color ?? '#ffffff',
    secondaryBgColor: tp.secondary_bg_color ?? '#161b22',
    colorScheme: tg?.colorScheme ?? 'dark',
  }
}

export function ready(): void {
  const tg = getTelegramWebApp()
  tg?.ready()
  tg?.expand()
}
