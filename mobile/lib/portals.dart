// Official government portal directory — ported verbatim from app.py
// (PROCUREMENT_PORTALS / RECRUITMENT_AUTHORITIES / STUDY_RESOURCES).
// Authoritative direct-routing links so users always reach the real source.

class Portal {
  final String label, url;
  const Portal(this.label, this.url);
}

const procurementPortals = <String, List<Portal>>{
  'National': [
    Portal('🏛 Central Public Procurement (CPPP)', 'https://eprocure.gov.in'),
    Portal('🛒 Government e-Marketplace (GeM)', 'https://gem.gov.in'),
  ],
  'Uttar Pradesh Network': [
    Portal('UP e-Procurement Portal', 'https://etender.up.nic.in'),
    Portal('UP Government Tenders Archive', 'http://tenders.up.nic.in'),
  ],
  'Chhattisgarh Network': [
    Portal('CG Integrated e-Procurement', 'https://eproc.cgstate.gov.in'),
    Portal('CG Government Tenders Portal', 'http://tenders.cg.gov.in'),
    Portal('CG Public Works Dept (PWD)', 'https://pwd.cg.nic.in'),
  ],
};

const recruitmentAuthorities = <String, List<Portal>>{
  'Uttar Pradesh Network': [
    Portal('UPPSC — Public Service Commission', 'https://uppsc.up.nic.in'),
    Portal('UPSSSC — Subordinate Services', 'http://upsssc.gov.in'),
    Portal('UPPRPB — Police Recruitment', 'https://www.upprpb.in'),
    Portal('UP Basic Education Board', 'http://upbasiceduboard.gov.in'),
  ],
  'Chhattisgarh Network': [
    Portal('CGPSC — Public Service Commission', 'https://psc.cg.gov.in'),
    Portal('CGPSC — Alternative Portal', 'https://ecgpsc.cgstate.gov.in'),
    Portal('CG Vyapam Board', 'https://vyapam.cgstate.gov.in'),
    Portal('CG Employment Exchange (Rojgar)', 'https://erojgar.cg.gov.in'),
    Portal('CG Police Headquarters', 'https://cgpolice.gov.in'),
    Portal('CG Directorate of Medical Education', 'https://cgdme.in'),
  ],
};

const studyResources = <String, List<Portal>>{
  'Free Learning Platforms': [
    Portal('📘 SWAYAM — Free Govt Courses', 'https://swayam.gov.in'),
    Portal('🎓 NPTEL — Engineering & Science', 'https://nptel.ac.in'),
    Portal('📗 NCERT — Free Textbooks', 'https://ncert.nic.in'),
    Portal('📚 National Digital Library', 'https://ndl.iitkgp.ac.in'),
  ],
  'Current Affairs & General Knowledge': [
    Portal('📰 PIB — Govt Press / Current Affairs', 'https://pib.gov.in'),
    Portal('🗞 Yojana / Kurukshetra', 'https://www.publicationsdivision.nic.in'),
    Portal('🏛 Chhattisgarh State Portal (CG GK)', 'https://cgstate.gov.in'),
    Portal('🏛 Uttar Pradesh State Portal (UP GK)', 'https://up.gov.in'),
  ],
};

/// Common UP/CG exams offered as quick-pick chips in the Study Matrix.
const commonExams = [
  'UPSC Civil Services',
  'UPPSC PCS',
  'CGPSC State Service',
  'UPSSSC PET',
  'CG Vyapam',
  'UP Police Constable',
  'CG Police Constable',
  'SSC CGL',
  'SSC CHSL',
  'Banking (IBPS/SBI)',
  'UP Lekhpal',
  'CTET / UPTET',
];
