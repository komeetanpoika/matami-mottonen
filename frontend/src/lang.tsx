import { createContext, ReactNode, useContext, useState } from 'react'
import { Lang, Strings, translations } from './translations'

interface LangCtx { lang: Lang; setLang: (l: Lang) => void; t: Strings }
const Ctx = createContext<LangCtx | null>(null)

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    try { return (localStorage.getItem('lang') as Lang) || 'en' } catch { return 'en' }
  })
  const set = (l: Lang) => { setLang(l); try { localStorage.setItem('lang', l) } catch { /* ignore */ } }
  return <Ctx.Provider value={{ lang, setLang: set, t: translations[lang] }}>{children}</Ctx.Provider>
}

export function useLang(): LangCtx {
  const v = useContext(Ctx)
  if (!v) throw new Error('useLang outside LangProvider')
  return v
}
