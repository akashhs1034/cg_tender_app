'use client'

import { createContext, useContext, useState, useCallback } from 'react'

export type Language = 'en' | 'hi'

interface LanguageContextValue {
  lang: Language
  setLang: (l: Language) => void
  t: (key: string) => string
}

// Flat string dictionary — add keys as the app grows
const translations: Record<Language, Record<string, string>> = {
  en: {
    dashboard: 'Dashboard',
    tenders: 'Tenders',
    jobs: 'Jobs',
    analytics: 'Analytics',
    our_website: 'Our Website',
    admin_queue: 'Admin Discovery Queue',
    sign_in: 'Sign In',
    sign_out: 'Sign Out',
    sign_up: 'Sign Up',
    get_started: 'Get Started',
    profile: 'Profile',
    settings: 'Settings',
    search_tenders: 'Search tenders, departments...',
    search_jobs: 'Search jobs, departments...',
    active_tenders: 'Active Tenders',
    active_jobs: 'Active Jobs',
    closing_soon: 'Closing Soon',
    new_today: 'New Today',
    view_details: 'View Details',
    prepare_bid: 'Prepare Bid',
    open_source: 'Open Source',
    check_match: 'Check My Match',
    recommended: 'Recommended',
    deadline: 'Deadline',
    vacancies: 'Vacancies',
    department: 'Department',
    location: 'Location',
    filters: 'Filters',
    showing: 'Showing',
    of: 'of',
    state: 'State',
    mode: 'Mode',
    category: 'Category',
    browse_as_guest: 'Browse as Guest',
    welcome_back: 'Welcome back',
    create_account: 'Create your account',
  },
  hi: {
    dashboard: 'डैशबोर्ड',
    tenders: 'टेंडर',
    jobs: 'नौकरियाँ',
    analytics: 'विश्लेषण',
    our_website: 'हमारी वेबसाइट',
    admin_queue: 'एडमिन डिस्कवरी कतार',
    sign_in: 'साइन इन',
    sign_out: 'साइन आउट',
    sign_up: 'साइन अप',
    get_started: 'शुरू करें',
    profile: 'प्रोफ़ाइल',
    settings: 'सेटिंग्स',
    search_tenders: 'टेंडर, विभाग खोजें...',
    search_jobs: 'नौकरी, विभाग खोजें...',
    active_tenders: 'सक्रिय टेंडर',
    active_jobs: 'सक्रिय नौकरियाँ',
    closing_soon: 'जल्द बंद',
    new_today: 'आज नए',
    view_details: 'विवरण देखें',
    prepare_bid: 'बोली तैयार करें',
    open_source: 'स्रोत खोलें',
    check_match: 'मिलान जाँचें',
    recommended: 'अनुशंसित',
    deadline: 'अंतिम तिथि',
    vacancies: 'रिक्तियाँ',
    department: 'विभाग',
    location: 'स्थान',
    filters: 'फ़िल्टर',
    showing: 'दिखा रहे हैं',
    of: 'में से',
    state: 'राज्य',
    mode: 'माध्यम',
    category: 'श्रेणी',
    browse_as_guest: 'अतिथि के रूप में देखें',
    welcome_back: 'वापसी पर स्वागत है',
    create_account: 'खाता बनाएँ',
  },
}

const LanguageContext = createContext<LanguageContextValue>({
  lang: 'en',
  setLang: () => {},
  t: (k) => k,
})

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>('en')

  const setLang = useCallback((l: Language) => {
    setLangState(l)
    if (typeof document !== 'undefined') {
      document.documentElement.lang = l === 'hi' ? 'hi' : 'en'
    }
  }, [])

  const t = useCallback(
    (key: string) => translations[lang][key] ?? translations['en'][key] ?? key,
    [lang]
  )

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  return useContext(LanguageContext)
}
