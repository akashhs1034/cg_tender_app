/**
 * Curated study resources per exam family — official portals, free YouTube
 * channels, and search-playlists. Matched to a job via keywords in its
 * title/department, so every notification gets a relevant study kit.
 *
 * YouTube links use stable channel handles or search URLs (never video IDs,
 * which rot). All channels are large, free, Hindi/English prep channels.
 */

export interface StudyLink {
  label: string
  url: string
  kind: 'official' | 'youtube' | 'syllabus' | 'practice'
}

export interface ExamResource {
  key: string
  name: string
  tip: string
  links: StudyLink[]
}

const yt = (q: string): string =>
  `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`

export const EXAM_RESOURCES: ExamResource[] = [
  {
    key: 'cgpsc',
    name: 'CGPSC (CG State Civil Services)',
    tip: 'Cover CG-specific GK (history, geography, tribes, schemes) alongside general studies — it decides the merit list.',
    links: [
      { label: 'CGPSC official (psc.cg.gov.in)', url: 'https://psc.cg.gov.in', kind: 'official' },
      { label: 'Drishti IAS (Hindi GS)', url: 'https://www.youtube.com/@DrishtiIASvideos', kind: 'youtube' },
      { label: 'StudyIQ IAS', url: 'https://www.youtube.com/@studyiqiasenglish', kind: 'youtube' },
      { label: 'CGPSC full prep playlists', url: yt('CGPSC preparation playlist'), kind: 'youtube' },
      { label: 'CG GK / छत्तीसगढ़ सामान्य ज्ञान', url: yt('Chhattisgarh GK CGPSC'), kind: 'youtube' },
      { label: 'Previous year papers', url: yt('CGPSC previous year question paper solution'), kind: 'practice' },
    ],
  },
  {
    key: 'cg_vyapam',
    name: 'CG Vyapam',
    tip: 'Vyapam papers are speed-focused — practice full mocks with a timer from week one.',
    links: [
      { label: 'CG Vyapam official', url: 'https://vyapam.cgstate.gov.in', kind: 'official' },
      { label: 'CG Vyapam prep playlists', url: yt('CG Vyapam exam preparation'), kind: 'youtube' },
      { label: 'Exampur', url: 'https://www.youtube.com/@Exampur', kind: 'youtube' },
      { label: 'CG GK for Vyapam', url: yt('CG Vyapam GK questions'), kind: 'practice' },
    ],
  },
  {
    key: 'uppsc',
    name: 'UPPSC (UP State Civil Services / RO-ARO)',
    tip: 'UP-special sections (UP GK, Hindi) are the score multipliers — do them daily, not at the end.',
    links: [
      { label: 'UPPSC official (uppsc.up.nic.in)', url: 'https://uppsc.up.nic.in', kind: 'official' },
      { label: 'Drishti IAS (Hindi GS)', url: 'https://www.youtube.com/@DrishtiIASvideos', kind: 'youtube' },
      { label: 'StudyIQ IAS', url: 'https://www.youtube.com/@studyiqiasenglish', kind: 'youtube' },
      { label: 'UPPSC PCS prep playlists', url: yt('UPPSC PCS preparation playlist'), kind: 'youtube' },
      { label: 'UP GK / उत्तर प्रदेश सामान्य ज्ञान', url: yt('UP GK UPPSC'), kind: 'youtube' },
      { label: 'Previous year papers', url: yt('UPPSC previous year paper solution'), kind: 'practice' },
    ],
  },
  {
    key: 'upsssc',
    name: 'UPSSSC (PET / Group C)',
    tip: 'Qualify PET first — it is the gateway to most UPSSSC mains. NCERT-level basics + speed math win here.',
    links: [
      { label: 'UPSSSC official (upsssc.gov.in)', url: 'https://upsssc.gov.in', kind: 'official' },
      { label: 'wifistudy', url: 'https://www.youtube.com/@wifistudy', kind: 'youtube' },
      { label: 'Exampur', url: 'https://www.youtube.com/@Exampur', kind: 'youtube' },
      { label: 'UPSSSC PET playlists', url: yt('UPSSSC PET complete preparation'), kind: 'youtube' },
      { label: 'PET mock tests', url: yt('UPSSSC PET mock test'), kind: 'practice' },
    ],
  },
  {
    key: 'police',
    name: 'Police / Constable / SI',
    tip: 'Split prep 50/50: written (GK, reasoning, law basics) and physical (running, standards) — start physical training now.',
    links: [
      { label: 'Police bharti playlists', url: yt('police constable bharti preparation'), kind: 'youtube' },
      { label: 'wifistudy', url: 'https://www.youtube.com/@wifistudy', kind: 'youtube' },
      { label: 'Exampur', url: 'https://www.youtube.com/@Exampur', kind: 'youtube' },
      { label: 'Reasoning practice', url: yt('reasoning tricks police exam'), kind: 'practice' },
    ],
  },
  {
    key: 'teaching',
    name: 'Teaching (TET / Shikshak Bharti)',
    tip: 'Child development & pedagogy carries the most weight — master it before content subjects.',
    links: [
      { label: 'CTET official', url: 'https://ctet.nic.in', kind: 'official' },
      { label: 'TET prep playlists', url: yt('TET exam preparation child development pedagogy'), kind: 'youtube' },
      { label: 'Adda247', url: 'https://www.youtube.com/@Adda247', kind: 'youtube' },
      { label: 'Previous TET papers', url: yt('TET previous year paper solution'), kind: 'practice' },
    ],
  },
  {
    key: 'ssc',
    name: 'SSC (CGL / CHSL / MTS)',
    tip: 'SSC is a maths+English speed game — daily quant practice beats weekend marathons.',
    links: [
      { label: 'SSC official (ssc.gov.in)', url: 'https://ssc.gov.in', kind: 'official' },
      { label: 'SSC Adda247', url: 'https://www.youtube.com/@SSCAdda247', kind: 'youtube' },
      { label: 'wifistudy', url: 'https://www.youtube.com/@wifistudy', kind: 'youtube' },
      { label: 'SSC CGL playlists', url: yt('SSC CGL complete preparation playlist'), kind: 'youtube' },
      { label: 'Quant practice', url: yt('SSC maths practice advanced'), kind: 'practice' },
    ],
  },
  {
    key: 'railway',
    name: 'Railway (RRB NTPC / Group D)',
    tip: 'General science + maths dominate RRB papers — revise class 9–10 science thoroughly.',
    links: [
      { label: 'RRB official (indianrailways.gov.in)', url: 'https://indianrailways.gov.in', kind: 'official' },
      { label: 'wifistudy', url: 'https://www.youtube.com/@wifistudy', kind: 'youtube' },
      { label: 'RRB NTPC playlists', url: yt('RRB NTPC complete preparation'), kind: 'youtube' },
      { label: 'General science practice', url: yt('railway general science questions'), kind: 'practice' },
    ],
  },
  {
    key: 'banking',
    name: 'Banking (IBPS / SBI)',
    tip: 'Sectional timing is everything — practice each section against the clock from day one.',
    links: [
      { label: 'IBPS official', url: 'https://www.ibps.in', kind: 'official' },
      { label: 'Adda247', url: 'https://www.youtube.com/@Adda247', kind: 'youtube' },
      { label: 'Banking prep playlists', url: yt('IBPS PO clerk complete preparation'), kind: 'youtube' },
      { label: 'Current affairs daily', url: yt('daily current affairs banking'), kind: 'practice' },
    ],
  },
  {
    key: 'general',
    name: 'General Government Exam Prep',
    tip: 'Whatever the exam: syllabus first, previous-year papers second, mocks weekly. Current affairs daily.',
    links: [
      { label: 'StudyIQ', url: 'https://www.youtube.com/@studyiqiasenglish', kind: 'youtube' },
      { label: 'wifistudy', url: 'https://www.youtube.com/@wifistudy', kind: 'youtube' },
      { label: 'Testbook', url: 'https://www.youtube.com/@Testbook', kind: 'youtube' },
      { label: 'Daily current affairs', url: yt('daily current affairs today'), kind: 'practice' },
      { label: 'NCERT books (free)', url: 'https://ncert.nic.in/textbook.php', kind: 'syllabus' },
    ],
  },
]

const MATCHERS: Array<{ key: string; kw: string[] }> = [
  { key: 'cg_vyapam', kw: ['vyapam'] },
  { key: 'cgpsc', kw: ['cgpsc', 'chhattisgarh public service', 'cg psc'] },
  { key: 'uppsc', kw: ['uppsc', 'up public service', 'ro/aro', 'ro aro', 'pcs'] },
  { key: 'upsssc', kw: ['upsssc', 'subordinate services', ' pet '] },
  { key: 'police', kw: ['police', 'constable', 'sub inspector', ' si ', 'aarakshi', 'आरक्षक', 'jail warder', 'home guard'] },
  { key: 'teaching', kw: ['teacher', 'tet', 'shikshak', 'शिक्षक', 'lecturer', 'professor', 'vyakhyata', 'व्याख्याता'] },
  { key: 'ssc', kw: ['ssc', 'staff selection'] },
  { key: 'railway', kw: ['railway', 'rrb', 'रेलवे'] },
  { key: 'banking', kw: ['bank', 'ibps', 'sbi'] },
]

/** Match a job to its exam resource kit (falls back to the general kit). */
export function matchExamResources(title: string, department?: string): ExamResource {
  const blob = ` ${title} ${department ?? ''} `.toLowerCase()
  for (const m of MATCHERS) {
    if (m.kw.some((k) => blob.includes(k))) {
      const found = EXAM_RESOURCES.find((r) => r.key === m.key)
      if (found) return found
    }
  }
  return EXAM_RESOURCES[EXAM_RESOURCES.length - 1]
}
