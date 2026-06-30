export type TenderMode = 'Online' | 'Offline' | 'Newspaper'
export type State = 'Chhattisgarh' | 'Uttar Pradesh'

export interface Tender {
  id: string
  title: string
  nitNumber: string
  department: string
  district: string
  state: State
  mode: TenderMode
  category: string
  estimatedValue: string
  emd: string
  deadline: string
  source: string
  aiMatchScore: number
  isRecommended?: boolean
  description: string
  eligibility: string[]
  documents: string[]
  riskLevel: 'Low' | 'Medium' | 'High'
  missingDocuments: string[]
  bidReadiness: number
}

export interface Job {
  id: string
  title: string
  advNumber: string
  department: string
  district: string
  state: State
  mode: TenderMode
  category: string
  qualification: string
  vacancies: number
  salary: string
  deadline: string
  matchScore: number
  isRecommended?: boolean
  description: string
  eligibility: string[]
  ageLimit: string
  examDate?: string
  selectionProcess: string[]
}

export const TENDER_CATEGORIES = [
  'All',
  'Road & Highway',
  'Bridge & Flyover',
  'Building Construction',
  'Water & Sanitation',
  'Irrigation & Dam',
  'Electrical & Solar',
  'IT & Electronics',
  'Railway & Metro',
  'Urban Development',
  'Forest & Environment',
  'Agriculture & Horticulture',
  'Health & Medical',
  'Education & Schools',
  'Mining & Minerals',
  'Transport & Logistics',
  'Printing & Stationery',
  'Security Services',
  'Consultancy & Survey',
  'Miscellaneous Works',
] as const

export const JOB_CATEGORIES = [
  'All',
  'Engineering',
  'Administrative',
  'Police & Defence',
  'Education',
  'Revenue & Administration',
  'Medical & Health',
  'Agriculture',
  'Forest & Wildlife',
  'Banking & Finance',
  'Law & Judiciary',
  'Transport',
  'IT & Technical',
  'Social Welfare',
  'Panchayati Raj',
  'Electricity & Power',
  'PWD & Infrastructure',
  'Clerical & Steno',
  'Sports & NCC',
  'Miscellaneous',
] as const

export type TenderCategory = typeof TENDER_CATEGORIES[number]
export type JobCategory = typeof JOB_CATEGORIES[number]

// ── State → District (mock data) ──────────────────────────────────────────────
// Powers the dependent State/District filters used across every tender & job
// listing/search surface. When live Supabase data is wired in, replace these
// arrays — the filter UI does not need to change.
export const CG_DISTRICTS = [
  'Balrampur', 'Raipur', 'Bilaspur', 'Durg', 'Rajnandgaon', 'Korba', 'Raigarh',
  'Surguja', 'Ambikapur', 'Jagdalpur', 'Kanker', 'Mahasamund', 'Janjgir-Champa',
  'Dhamtari',
] as const

export const UP_DISTRICTS = [
  'Lucknow', 'Kanpur Nagar', 'Varanasi', 'Prayagraj', 'Ghaziabad',
  'Noida / Gautam Buddha Nagar', 'Agra', 'Meerut', 'Gorakhpur', 'Bareilly',
  'Aligarh', 'Jhansi', 'Ayodhya', 'Moradabad',
] as const

export const DISTRICTS_BY_STATE: Record<State, readonly string[]> = {
  'Chhattisgarh': CG_DISTRICTS,
  'Uttar Pradesh': UP_DISTRICTS,
}

/**
 * Districts to show for a given State filter selection.
 * - A specific state returns that state's districts.
 * - 'All' (no state chosen) returns [] so the District dropdown shows only
 *   "All Districts" until a state is picked.
 */
export function getDistricts(state: State | 'All'): readonly string[] {
  if (state === 'Chhattisgarh' || state === 'Uttar Pradesh') return DISTRICTS_BY_STATE[state]
  return []
}

export const tenders: Tender[] = [
  {
    id: 'T001',
    title: 'Construction of NH-130C Road Widening Project — Phase II',
    nitNumber: 'NIT/PWD/CG/2025/0412',
    department: 'Public Works Department, Chhattisgarh',
    district: 'Raipur',
    state: 'Chhattisgarh',
    mode: 'Online',
    category: 'Road & Highway',
    estimatedValue: '₹24.6 Cr',
    emd: '₹49,200',
    deadline: '15 Jul 2025',
    source: 'etender.cg.gov.in',
    aiMatchScore: 92,
    isRecommended: true,
    description:
      'Widening and strengthening of NH-130C from 2-lane to 4-lane configuration covering 18.4 km stretch in Raipur district. Work includes drainage, signage, and service roads.',
    eligibility: [
      'Class-A Civil Works registered contractor',
      'Minimum 3 similar projects of ≥ ₹8 Cr in last 5 years',
      'Annual turnover ≥ ₹12 Cr in last 3 financial years',
      'Valid GST registration',
    ],
    documents: ['Company PAN', 'GST Certificate', 'Work Experience Certificates', 'Audited Balance Sheets (3 years)', 'Bank Solvency Certificate'],
    riskLevel: 'Low',
    missingDocuments: ['Bank Solvency Certificate'],
    bidReadiness: 87,
  },
  {
    id: 'T002',
    title: 'Smart City CCTV Surveillance Network Installation — Lucknow Phase 3',
    nitNumber: 'NIT/LSMC/UP/2025/0089',
    department: 'Lucknow Smart City Mission',
    district: 'Lucknow',
    state: 'Uttar Pradesh',
    mode: 'Online',
    category: 'IT & Electronics',
    estimatedValue: '₹8.2 Cr',
    emd: '₹16,400',
    deadline: '22 Jul 2025',
    source: 'etender.up.gov.in',
    aiMatchScore: 76,
    isRecommended: false,
    description:
      'Supply, installation, testing, and commissioning of 1,200 CCTV cameras with central command & control centre integration in Lucknow city zone.',
    eligibility: [
      'Registered IT/Electronics contractor',
      'ISO 9001:2015 certified',
      'Prior experience in smart city or surveillance projects',
    ],
    documents: ['Company Registration', 'ISO Certificate', 'Experience Certificates', 'GST Certificate'],
    riskLevel: 'Medium',
    missingDocuments: ['ISO Certificate', 'Smart City Project Experience Letter'],
    bidReadiness: 64,
  },
  {
    id: 'T003',
    title: 'Construction of Primary Health Centre Building — Korba District',
    nitNumber: 'NIT/CHD/CG/2025/0331',
    department: 'Health & Family Welfare Dept., CG',
    district: 'Korba',
    state: 'Chhattisgarh',
    mode: 'Offline',
    category: 'Building Construction',
    estimatedValue: '₹1.85 Cr',
    emd: '₹3,700',
    deadline: '10 Jul 2025',
    source: 'District Health Office, Korba',
    aiMatchScore: 84,
    isRecommended: true,
    description:
      'Construction of G+1 Primary Health Centre building with OPD, IPD wards, lab, pharmacy, and staff quarters at village Pathra.',
    eligibility: [
      'Class-B or above contractor registration',
      'Similar PHC/institutional building experience',
    ],
    documents: ['Registration Certificate', 'PAN', 'GST', 'Past Experience'],
    riskLevel: 'Low',
    missingDocuments: [],
    bidReadiness: 95,
  },
  {
    id: 'T004',
    title: 'Supply of Solar-Powered Street Lights — Varanasi Municipal',
    nitNumber: 'NIT/VMC/UP/2025/0217',
    department: 'Varanasi Municipal Corporation',
    district: 'Varanasi',
    state: 'Uttar Pradesh',
    mode: 'Online',
    category: 'Electrical & Solar',
    estimatedValue: '₹3.4 Cr',
    emd: '₹6,800',
    deadline: '28 Jul 2025',
    source: 'etender.up.gov.in',
    aiMatchScore: 61,
    isRecommended: false,
    description:
      'Supply, installation, and maintenance of 2,400 solar-powered LED street lights with remote monitoring system in Varanasi city.',
    eligibility: [
      'MNRE registered solar equipment supplier',
      'Class-A electrical contractor',
    ],
    documents: ['MNRE Registration', 'Electrical License', 'GST', 'Experience Certificates'],
    riskLevel: 'High',
    missingDocuments: ['MNRE Registration', 'Electrical License (UP)'],
    bidReadiness: 45,
  },
  {
    id: 'T005',
    title: 'Repair and Renovation of Public School Buildings — 32 Schools',
    nitNumber: 'NIT/EDU/CG/2025/0512',
    department: 'School Education Dept., Chhattisgarh',
    district: 'Bilaspur',
    state: 'Chhattisgarh',
    mode: 'Newspaper',
    category: 'Building Construction',
    estimatedValue: '₹4.1 Cr',
    emd: '₹8,200',
    deadline: '5 Jul 2025',
    source: 'Dainik Bhaskar, Raipur Edition',
    aiMatchScore: 88,
    isRecommended: true,
    description:
      'Repair, renovation, and minor construction works across 32 public school buildings in Bilaspur district including roofing, flooring, sanitation blocks.',
    eligibility: [
      'Class-B civil contractor',
      'Prior institutional building experience',
    ],
    documents: ['Registration', 'PAN', 'GST', 'Past Work Orders'],
    riskLevel: 'Low',
    missingDocuments: [],
    bidReadiness: 91,
  },
  {
    id: 'T006',
    title: 'Water Supply Pipeline Network — Gorakhpur Urban Area',
    nitNumber: 'NIT/JICA/UP/2025/0041',
    department: 'Jal Nigam, Uttar Pradesh',
    district: 'Gorakhpur',
    state: 'Uttar Pradesh',
    mode: 'Online',
    category: 'Water & Sanitation',
    estimatedValue: '₹15.7 Cr',
    emd: '₹31,400',
    deadline: '18 Jul 2025',
    source: 'etender.up.gov.in',
    aiMatchScore: 70,
    isRecommended: false,
    description:
      'Laying of 48 km water supply distribution pipeline and 12 service reservoirs under AMRUT 2.0 scheme in Gorakhpur urban area.',
    eligibility: [
      'Class-A contractor with water works experience',
      'Prior pipeline project of ≥ ₹5 Cr',
    ],
    documents: ['Registration', 'Experience Certificates', 'Financial Statements'],
    riskLevel: 'Medium',
    missingDocuments: ['AMRUT Empanelment Letter'],
    bidReadiness: 72,
  },
]

export const jobs: Job[] = [
  {
    id: 'J001',
    title: 'Assistant Engineer (Civil) — Grade 1',
    advNumber: 'ADV/CGPSC/2025/AE-031',
    department: 'Chhattisgarh Public Service Commission',
    district: 'Raipur',
    state: 'Chhattisgarh',
    mode: 'Online',
    category: 'Engineering',
    qualification: 'B.E./B.Tech Civil Engineering',
    vacancies: 342,
    salary: '₹56,100 – ₹1,77,500/month',
    deadline: '20 Jul 2025',
    matchScore: 91,
    isRecommended: true,
    description:
      'CGPSC recruitment for Assistant Engineer (Civil) Grade-1 under various state departments. Selection through written examination followed by interview.',
    eligibility: [
      'B.E./B.Tech in Civil Engineering from recognized university',
      'Age: 21–35 years (relaxation for SC/ST/OBC as per norms)',
      'Domicile of Chhattisgarh preferred',
      'Valid Aadhaar card',
    ],
    ageLimit: '21–35 years',
    examDate: '14 Sep 2025',
    selectionProcess: ['Preliminary Exam', 'Main Exam', 'Interview', 'Document Verification'],
  },
  {
    id: 'J002',
    title: 'Sub-Inspector (Civil Police) — UP Police',
    advNumber: 'ADV/UPPBPB/2025/SI-112',
    department: 'UP Police Recruitment & Promotion Board',
    district: 'Lucknow',
    state: 'Uttar Pradesh',
    mode: 'Online',
    category: 'Police & Defence',
    qualification: 'Bachelor\'s Degree (Any Stream)',
    vacancies: 9534,
    salary: '₹35,400 – ₹1,12,400/month',
    deadline: '31 Jul 2025',
    matchScore: 68,
    isRecommended: false,
    description:
      'Mass recruitment for Sub-Inspector (Civil Police) under Uttar Pradesh Police. One of the largest police recruitments in 2025.',
    eligibility: [
      'Bachelor\'s degree from any recognized university',
      'Age: 21–28 years (relaxation as per applicable norms)',
      'Physical fitness standards as per UPPBPB norms',
    ],
    ageLimit: '21–28 years',
    examDate: '5 Oct 2025',
    selectionProcess: ['Written Exam', 'Physical Efficiency Test', 'Medical Exam', 'Document Verification'],
  },
  {
    id: 'J003',
    title: 'Panchayat Sachiv (Panchayat Secretary) — CG',
    advNumber: 'ADV/CGVYAPAM/2025/PS-078',
    department: 'CG Vyapam (Professional Examination Board)',
    district: 'Multiple Districts',
    state: 'Chhattisgarh',
    mode: 'Online',
    category: 'Administrative',
    qualification: 'Class 12 / Higher Secondary',
    vacancies: 1234,
    salary: '₹19,500 – ₹62,000/month',
    deadline: '12 Jul 2025',
    matchScore: 79,
    isRecommended: true,
    description:
      'CG Vyapam recruitment for Panchayat Sachiv posts across multiple districts in Chhattisgarh state. Computer proficiency required.',
    eligibility: [
      '10+2 from recognized board',
      'Computer knowledge certificate (CPCT preferred)',
      'Age: 18–35 years',
      'CG domicile required',
    ],
    ageLimit: '18–35 years',
    examDate: '28 Aug 2025',
    selectionProcess: ['Written Exam', 'Computer Proficiency Test', 'Document Verification'],
  },
  {
    id: 'J004',
    title: 'Upper Primary Teacher (Science/Maths) — UP Supertet',
    advNumber: 'ADV/UPSESSB/2025/UPT-504',
    department: 'UP Basic Education Board',
    district: 'Multiple Districts',
    state: 'Uttar Pradesh',
    mode: 'Offline',
    category: 'Education',
    qualification: 'B.Sc + B.Ed / Integrated B.El.Ed',
    vacancies: 2673,
    salary: '₹44,900 – ₹1,42,400/month',
    deadline: '25 Jul 2025',
    matchScore: 85,
    isRecommended: true,
    description:
      'Upper Primary Teacher recruitment for Science/Mathematics stream under UP Basic Education Board. TET/CTET qualified candidates preferred.',
    eligibility: [
      'B.Sc with B.Ed or Integrated B.El.Ed',
      'TET/CTET qualified',
      'Age: 21–40 years',
      'UP domicile certificate',
    ],
    ageLimit: '21–40 years',
    examDate: '20 Sep 2025',
    selectionProcess: ['SUPERTET Written Exam', 'Merit List', 'Document Verification', 'Joining'],
  },
  {
    id: 'J005',
    title: 'Junior Engineer (Electrical) — Chhattisgarh State Power',
    advNumber: 'ADV/CSPDCL/2025/JE-023',
    department: 'CSPDCL (CG State Power Distribution)',
    district: 'Raipur',
    state: 'Chhattisgarh',
    mode: 'Newspaper',
    category: 'Engineering',
    qualification: 'Diploma in Electrical Engineering',
    vacancies: 187,
    salary: '₹31,500 – ₹1,00,000/month',
    deadline: '8 Jul 2025',
    matchScore: 72,
    isRecommended: false,
    description:
      'CSPDCL recruitment for Junior Engineer Electrical posts. Candidates with ITI (Electrician) trade certificate may also apply.',
    eligibility: [
      'Diploma in Electrical Engineering from recognized polytechnic',
      'Age: 18–30 years',
      'CG domicile preferred',
    ],
    ageLimit: '18–30 years',
    examDate: '15 Aug 2025',
    selectionProcess: ['Written Exam', 'Skill Test', 'Document Verification'],
  },
  {
    id: 'J006',
    title: 'Naib Tehsildar (Revenue Department) — UP Revenue Board',
    advNumber: 'ADV/UPPSC/2025/NT-289',
    department: 'UP Public Service Commission',
    district: 'Prayagraj',
    state: 'Uttar Pradesh',
    mode: 'Online',
    category: 'Revenue & Administration',
    qualification: 'Bachelor\'s Degree (Any Stream)',
    vacancies: 408,
    salary: '₹44,900 – ₹1,42,400/month',
    deadline: '4 Aug 2025',
    matchScore: 63,
    isRecommended: false,
    description:
      'UPPSC recruitment for Naib Tehsildar (Assistant Revenue Officer) posts under UP Revenue Department.',
    eligibility: [
      'Bachelor\'s degree from any recognized university',
      'Age: 21–40 years (relaxation as per norms)',
      'Knowledge of Hindi in Devanagari script',
    ],
    ageLimit: '21–40 years',
    examDate: '12 Nov 2025',
    selectionProcess: ['Preliminary Exam', 'Main Exam', 'Interview'],
  },
]

export const dashboardStats = {
  activeTenders: 1248,
  activeJobs: 3641,
  offlineNewspaper: 312,
  corrigendums: 47,
  closingSoon: 89,
  newToday: 34,
  cgCount: 2108,
  upCount: 2793,
}

export const adminQueue = [
  {
    id: 'AQ001',
    source: 'Dainik Bhaskar — Raipur Edition',
    type: 'Newspaper',
    state: 'Chhattisgarh',
    discoveredAt: '2025-07-01 09:14',
    opportunities: 7,
    confidenceScore: 91,
    status: 'Pending' as const,
    captchaRequired: false,
    notes: 'Multiple tender notices on page 4 and 6.',
  },
  {
    id: 'AQ002',
    source: 'etender.cg.gov.in — New Listings',
    type: 'Online',
    state: 'Chhattisgarh',
    discoveredAt: '2025-07-01 08:55',
    opportunities: 23,
    confidenceScore: 98,
    status: 'Approved' as const,
    captchaRequired: false,
    notes: 'Auto-parsed successfully.',
  },
  {
    id: 'AQ003',
    source: 'Amar Ujala — Lucknow Edition',
    type: 'Newspaper',
    state: 'Uttar Pradesh',
    discoveredAt: '2025-07-01 08:30',
    opportunities: 4,
    confidenceScore: 74,
    status: 'Pending' as const,
    captchaRequired: false,
    notes: 'Low confidence — requires manual review.',
  },
  {
    id: 'AQ004',
    source: 'gem.gov.in — Public e-Marketplace',
    type: 'Online',
    state: 'Uttar Pradesh',
    discoveredAt: '2025-07-01 07:45',
    opportunities: 0,
    confidenceScore: 0,
    status: 'CaptchaRequired' as const,
    captchaRequired: true,
    notes: 'CAPTCHA encountered during scraping.',
  },
  {
    id: 'AQ005',
    source: 'Navbharat — Bilaspur Edition',
    type: 'Newspaper',
    state: 'Chhattisgarh',
    discoveredAt: '2025-06-30 18:10',
    opportunities: 2,
    confidenceScore: 65,
    status: 'Rejected' as const,
    captchaRequired: false,
    notes: 'Duplicate entries already in database.',
  },
  {
    id: 'AQ006',
    source: 'etender.up.gov.in — New Listings',
    type: 'Online',
    state: 'Uttar Pradesh',
    discoveredAt: '2025-06-30 17:30',
    opportunities: 31,
    confidenceScore: 97,
    status: 'Approved' as const,
    captchaRequired: false,
    notes: 'Batch approved — all 31 listings ingested.',
  },
]
