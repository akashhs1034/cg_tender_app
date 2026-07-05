'use client'

import { createContext, useContext, useState, useCallback, useEffect } from 'react'

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
    admin_health: 'Source Health',
    admin_queue: 'Admin Discovery Queue',
    active_tenders_across: 'active tenders across CG & UP',
    active_jobs_across: 'active jobs across CG & UP',
    search_filter_full: 'search and filter across the full database.',
    prev: 'Prev',
    next: 'Next',
    page: 'Page',
    plan_prep: 'Plan your preparation for upcoming government exams',
    plan_prep_long: 'Plan your preparation for upcoming government exams — filter by state, district, category or advertisement number.',
    study_plan_resources: 'Study Plan & Resources',
    study_resources: 'Study Resources',
    study_resources_sub: 'Free preparation material for every major CG & UP government exam — official portals, YouTube channels and practice links.',
    exam_date: 'Exam Date',
    apply_before: 'Apply Before',
    view_job: 'View Job',
    apply: 'Apply',
    posts: 'posts',
    notifications: 'notifications',
    search_adv: 'Search by Advertisement number…',
    job_category: 'Job Category',
    all_categories: 'All Categories',
    no_notifications: 'No notifications available right now',
    check_back: 'Please check back after the next data sync.',
    no_match_selection: 'No notifications match your selection',
    adjust_selection: 'Adjust the state, district, category, or advertisement search',
    study_plan: 'Study plan',
    show_all_notifications: 'Show all notifications',
    dashboard_sub: 'Your opportunity overview',
    tenders_sub: 'Browse live government tenders',
    jobs_sub: 'Browse live government jobs',
    all: 'All',
    online: 'Online',
    offline: 'Offline',
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
    saved: 'Saved',
    district: 'District',
    all_districts: 'All Districts',
    select_state_first: 'Select a state first',
    reset_filters: 'Reset filters',
    no_tenders_match: 'No tenders match your filters',
    no_jobs_match: 'No jobs match your filters',
    try_adjusting: 'Try adjusting your search or filters',
    no_tenders_available: 'No tenders available right now',
    no_jobs_available: 'No jobs available right now',
    analyze: 'Analyze',
    bid_document: 'Bid Document',
    save: 'Save',
    share: 'Share',
    exam_planner: 'Exam Planner',
    check_eligibility: 'Check Eligibility',
    government_tenders: 'Government Tenders',
    government_jobs: 'Government Jobs',
    tender_portal: 'Tender Portal',
    bid_documents: 'Bid Documents',
    qualification: 'Qualification',
  },
  hi: {
    dashboard: 'डैशबोर्ड',
    tenders: 'टेंडर',
    jobs: 'नौकरियाँ',
    analytics: 'विश्लेषण',
    our_website: 'हमारी वेबसाइट',
    admin_health: 'स्रोत स्थिति',
    admin_queue: 'एडमिन डिस्कवरी कतार',
    active_tenders_across: 'छत्तीसगढ़ और उ.प्र. में सक्रिय टेंडर',
    active_jobs_across: 'छत्तीसगढ़ और उ.प्र. में सक्रिय नौकरियाँ',
    search_filter_full: 'पूरे डेटाबेस में खोजें और फ़िल्टर करें।',
    prev: 'पिछला',
    next: 'अगला',
    page: 'पृष्ठ',
    plan_prep: 'आगामी सरकारी परीक्षाओं की तैयारी की योजना बनाएं',
    plan_prep_long: 'आगामी सरकारी परीक्षाओं की तैयारी की योजना बनाएं — राज्य, ज़िला, श्रेणी या विज्ञापन संख्या से फ़िल्टर करें।',
    study_plan_resources: 'अध्ययन योजना और संसाधन',
    study_resources: 'अध्ययन संसाधन',
    study_resources_sub: 'छत्तीसगढ़ और उ.प्र. की हर प्रमुख सरकारी परीक्षा के लिए मुफ़्त तैयारी सामग्री — आधिकारिक पोर्टल, YouTube चैनल और अभ्यास लिंक।',
    exam_date: 'परीक्षा तिथि',
    apply_before: 'अंतिम तिथि',
    view_job: 'नौकरी देखें',
    apply: 'आवेदन करें',
    posts: 'पद',
    notifications: 'अधिसूचनाएँ',
    search_adv: 'विज्ञापन संख्या से खोजें…',
    job_category: 'नौकरी श्रेणी',
    all_categories: 'सभी श्रेणियाँ',
    no_notifications: 'अभी कोई अधिसूचना उपलब्ध नहीं है',
    check_back: 'कृपया अगले डेटा सिंक के बाद फिर देखें।',
    no_match_selection: 'आपके चयन से कोई अधिसूचना मेल नहीं खाती',
    adjust_selection: 'राज्य, ज़िला, श्रेणी या विज्ञापन खोज बदलकर देखें',
    study_plan: 'अध्ययन योजना',
    show_all_notifications: 'सभी अधिसूचनाएँ दिखाएँ',
    dashboard_sub: 'आपके अवसरों का अवलोकन',
    tenders_sub: 'लाइव सरकारी टेंडर ब्राउज़ करें',
    jobs_sub: 'लाइव सरकारी नौकरियाँ ब्राउज़ करें',
    all: 'सभी',
    online: 'ऑनलाइन',
    offline: 'ऑफ़लाइन',
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
    saved: 'सहेजे गए',
    district: 'ज़िला',
    all_districts: 'सभी ज़िले',
    select_state_first: 'पहले राज्य चुनें',
    reset_filters: 'फ़िल्टर रीसेट करें',
    no_tenders_match: 'आपके फ़िल्टर से कोई टेंडर मेल नहीं खाता',
    no_jobs_match: 'आपके फ़िल्टर से कोई नौकरी मेल नहीं खाती',
    try_adjusting: 'अपनी खोज या फ़िल्टर बदलकर देखें',
    no_tenders_available: 'अभी कोई टेंडर उपलब्ध नहीं है',
    no_jobs_available: 'अभी कोई नौकरी उपलब्ध नहीं है',
    analyze: 'विश्लेषण',
    bid_document: 'बोली दस्तावेज़',
    save: 'सहेजें',
    share: 'साझा करें',
    exam_planner: 'परीक्षा योजनाकार',
    check_eligibility: 'पात्रता जाँचें',
    government_tenders: 'सरकारी टेंडर',
    government_jobs: 'सरकारी नौकरियाँ',
    tender_portal: 'टेंडर पोर्टल',
    bid_documents: 'बोली दस्तावेज़',
    qualification: 'योग्यता',
  },
}

const LanguageContext = createContext<LanguageContextValue>({
  lang: 'en',
  setLang: () => {},
  t: (k) => k,
})

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>('en')

  // Restore the saved language choice on mount.
  useEffect(() => {
    const saved = typeof window !== 'undefined' ? window.localStorage.getItem('opporta:lang') : null
    if (saved === 'hi' || saved === 'en') {
      setLangState(saved)
      document.documentElement.lang = saved
    }
  }, [])

  const setLang = useCallback((l: Language) => {
    setLangState(l)
    if (typeof document !== 'undefined') {
      document.documentElement.lang = l === 'hi' ? 'hi' : 'en'
      window.localStorage.setItem('opporta:lang', l)
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
