// Opporta Intelligence — client-side scoring + AI fallbacks.
//
// The web app's 6-dimension tender scoring (evaluator.score_opportunity) is
// PURELY RULE-BASED, so it's ported here verbatim and runs offline — no edge
// function, no key. The study-plan + resume analysers have a rule-based fallback
// here too, so the features work even before the `intelligence` Edge Function is
// deployed; when it is, data.dart prefers the AI result.
import 'data.dart';

// ── small local helpers (data.dart's are private to that file) ────────────────
double _num(dynamic v) {
  if (v == null) return 0;
  return double.tryParse('$v'.replaceAll(',', '').replaceAll(RegExp(r'[^0-9.\-]'), '')) ?? 0;
}

int _int(dynamic v) => _num(v).toInt();

String _str(dynamic v) => (v == null) ? '' : '$v'.trim();

/// Convert a messy EMD / money string into LAKHS (mirrors core.parse_value_to_lakhs, simplified).
double? _toLakhs(String raw) {
  final s = raw.toLowerCase().trim();
  if (s.isEmpty || ['n/a', 'nan', 'none', 'exempted', '-'].contains(s)) return null;
  final m = RegExp(r'([0-9][0-9,]*\.?[0-9]*)').firstMatch(s);
  if (m == null) return null;
  final n = double.tryParse(m.group(1)!.replaceAll(',', ''));
  if (n == null) return null;
  if (s.contains('cr')) return n * 100; // crore -> lakhs
  if (s.contains('lakh') || s.contains(' l') || s.endsWith('l')) return n;
  if (n > 100000) return n / 100000; // absolute rupees -> lakhs
  return n;
}

const _classRank = {
  'open': 0, 'unlimited': 5,
  'class a': 4, 'a': 4, 'class b': 3, 'b': 3,
  'class c': 2, 'c': 2, 'class d': 1, 'd': 1, 'class e': 1, 'e': 1,
};
int _rank(String? label) => _classRank[(label ?? '').trim().toLowerCase()] ?? 0;

int _expYears(String label) {
  final s = label.toLowerCase();
  if (s.contains('5+') || s.contains('5 +')) return 5;
  if (s.contains('3-5') || s.contains('3+')) return 3;
  if (s.contains('1-3')) return 1;
  return 0;
}

const _priorityKw = [
  'coal', 'coal transportation', 'loading', 'unloading', 'railway siding',
  'dumper hiring', 'truck hiring', 'vehicle hiring', 'manpower supply',
  'security services', 'housekeeping', 'mining', 'freight movement',
  'material transportation', 'logistics', 'warehousing', 'transport',
  'industrial transportation', 'road construction',
];

const _highReliabilityOrgs = [
  'secl', 'cil', 'coal india', 'ntpc', 'bhel', 'bpcl', 'hpcl', 'ongc',
  'nhpc', 'nhai', 'ircon', 'rites', 'central', 'cpwd', 'national',
];
const _medReliabilityOrgs = [
  'state', 'pwd', 'phed', 'phd', 'cspdcl', 'uppcl', 'jal', 'nagar',
  'municipal', 'district', 'collector',
];
const _nicheCats = ['Coal & Mining', 'Transport', 'Manpower Supply', 'Warehousing'];
const _commodityCats = ['Civil Infrastructure', 'Electrical & Energy', 'Water & Irrigation'];

/// One scored dimension: a 0-100 value + the reasons that produced it.
class ScoreDimension {
  final String key;
  final String label;
  final int score;
  final List<String> reasons;
  const ScoreDimension(this.key, this.label, this.score, this.reasons);
}

/// Full 6-dimension opportunity score for a tender + the contractor.
class TenderScore {
  final List<ScoreDimension> dimensions;
  TenderScore(this.dimensions);

  /// Overall = mean of the six dimensions (competition is "risk", so inverted).
  int get overall {
    if (dimensions.isEmpty) return 0;
    var sum = 0;
    for (final d in dimensions) {
      sum += d.key == 'competition' ? (100 - d.score) : d.score;
    }
    return (sum / dimensions.length).round();
  }

  String get verdict {
    final o = overall;
    if (o >= 75) return 'Strong opportunity — worth bidding';
    if (o >= 55) return 'Decent fit — review details before bidding';
    if (o >= 40) return 'Marginal — bid only if capacity is free';
    return 'Weak fit — likely not worth the effort';
  }
}

/// Port of evaluator.score_opportunity — pure rule-based, no AI.
class Scorer {
  static bool _highPriority(Tender t) {
    final text =
        '${t.title} ${t.category} ${_str(t.raw['description'])} ${t.org}'.toLowerCase();
    return _priorityKw.any(text.contains);
  }

  static TenderScore score(Tender t, Map<String, dynamic> profile) {
    final org = t.org.toLowerCase();
    final cat = t.category;
    final val = t.valueLakhs;
    final emdRaw = _str(t.raw['emd']);
    final turnover = _num(profile['turnover_lakhs']);
    final expYrs = _int(profile['experience_years']);
    final tText = '${t.title} $cat ${_str(t.raw['description'])}'.toLowerCase();
    final highPri = _highPriority(t);

    // ── Lead ──────────────────────────────────────────────────────────────
    var lead = 50;
    final leadR = <String>[];
    if (highPri) {
      lead += 20;
      leadR.add('Matches your priority sectors (coal/transport/logistics)');
    }
    if (val > 0) {
      if (val <= turnover * 0.3) {
        lead += 15;
        leadR.add('Contract size fits your capacity');
      } else if (val <= turnover) {
        lead += 8;
        leadR.add('Contract is sizeable but reachable');
      } else if (val > turnover * 2) {
        lead -= 15;
        leadR.add('Contract likely exceeds your capacity');
      }
    }
    final emdNum = _toLakhs(emdRaw);
    if (emdNum != null && val > 0) {
      final emdPct = (emdNum / val) * 100;
      if (emdPct <= 2) {
        lead += 8;
        leadR.add('Low EMD relative to contract value');
      } else if (emdPct > 5) {
        lead -= 8;
        leadR.add('High EMD requirement');
      }
    }
    if (t.contractorClass.isEmpty) {
      lead += 5;
      leadR.add('No contractor class restriction stated');
    }
    lead = lead.clamp(0, 100);

    // ── Profitability ───────────────────────────────────────────────────────
    var profit = 45;
    final profitR = <String>[];
    if (_nicheCats.contains(cat)) {
      profit += 20;
      profitR.add('$cat typically carries strong margins');
    }
    if (tText.contains('coal') || tText.contains('mining')) {
      profit += 12;
      profitR.add('Coal/mining contracts often carry 15–25% margins');
    }
    if (tText.contains('transport') || tText.contains('vehicle')) {
      profit += 8;
      profitR.add('Transport/hiring contracts: low overhead, fast cash');
    }
    if (val >= 50) {
      profit += 10;
      profitR.add('Contract value justifies mobilisation cost');
    } else if (val > 0 && val < 5) {
      profit -= 10;
      profitR.add('Small contract — margin may be tight');
    }
    if (tText.contains('annual') || tText.contains('year')) {
      profit += 8;
      profitR.add('Recurring/annual contract = predictable revenue');
    }
    profit = profit.clamp(0, 100);

    // ── Qualification probability ────────────────────────────────────────────
    var qual = 60;
    final qualR = <String>[];
    final reqRank = _rank(t.contractorClass);
    if (reqRank == 0) {
      qual += 15;
      qualR.add('No contractor class requirement');
    } else if (_rank(_str(profile['contractor_class'])) >= reqRank) {
      qual += 12;
      qualR.add('You meet class requirement (${t.contractorClass})');
    } else {
      qual -= 25;
      qualR.add('Class mismatch — needs ${t.contractorClass}');
    }
    final reqExp = _expYears(_str(t.raw['experience']));
    if (reqExp == 0) {
      qual += 8;
      qualR.add('No experience barrier');
    } else if (expYrs >= reqExp) {
      qual += 10;
      qualR.add('Your ${expYrs}yr experience meets ${reqExp}yr requirement');
    } else {
      qual -= 15;
      qualR.add('Experience gap: need ${reqExp}yr, have ${expYrs}yr');
    }
    if (val > 0 && turnover > 0 && val <= turnover * 2.5) {
      qual += 8;
      qualR.add('Turnover likely sufficient for EMD eligibility');
    }
    qual = qual.clamp(0, 100);

    // ── Competition risk (higher = harder to win) ─────────────────────────────
    var comp = 50;
    final compR = <String>[];
    if (_nicheCats.contains(cat)) {
      comp -= 20;
      compR.add('Niche category ($cat) = fewer qualified bidders');
    }
    if (_commodityCats.contains(cat)) {
      comp += 15;
      compR.add('$cat attracts many bidders');
    }
    if (val > 500) {
      comp += 15;
      compR.add('High-value contracts attract large firms');
    } else if (val > 0 && val < 20) {
      comp -= 8;
      compR.add('Small contract — less attractive to large players');
    }
    if (org.contains('secl') || org.contains('coal india') || org.contains('cil')) {
      comp -= 10;
      compR.add('SECL/CIL contracts favour experienced mining contractors');
    }
    comp = comp.clamp(0, 100);

    // ── Payment reliability ───────────────────────────────────────────────────
    var pay = 55;
    final payR = <String>[];
    if (_highReliabilityOrgs.any(org.contains)) {
      pay = 85;
      payR.add('Central PSU / national body — strong payment track record');
    } else if (_medReliabilityOrgs.any(org.contains)) {
      pay = 65;
      payR.add('State department — generally reliable, sometimes delayed');
    } else {
      pay = 55;
      payR.add("Check department's payment history before bidding");
    }
    if (org.contains('secl') || org.contains('cil')) {
      pay = 90;
      payR.add('Coal India subsidiaries are known for timely payments');
    }
    pay = pay.clamp(0, 100);

    // ── Strategic value ───────────────────────────────────────────────────────
    var strat = 50;
    final stratR = <String>[];
    if (highPri) {
      strat += 20;
      stratR.add('Aligns with your core business sectors');
    }
    if (org.contains('secl') || org.contains('cil')) {
      strat += 20;
      stratR.add('SECL/CIL vendor empanelment opens repeat business pipeline');
    }
    if (tText.contains('annual') || tText.contains('year') || tText.contains('rate')) {
      strat += 10;
      stratR.add('Rate contract / annual order = recurring revenue');
    }
    if (val >= 100) {
      strat += 8;
      stratR.add('Large contract builds portfolio credentials');
    }
    strat = strat.clamp(0, 100);

    return TenderScore([
      ScoreDimension('lead', '🎯 Lead score', lead, leadR),
      ScoreDimension('profit', '💰 Profitability', profit, profitR),
      ScoreDimension('qualification', '✅ Qualification', qual, qualR),
      ScoreDimension('competition', '⚔ Competition risk', comp, compR),
      ScoreDimension('payment', '🏦 Payment reliability', pay, payR),
      ScoreDimension('strategic', '♟ Strategic value', strat, stratR),
    ]);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Resume ↔ job match (keyword fallback; AI version comes from the Edge Function)
// ─────────────────────────────────────────────────────────────────────────────
class ResumeMatch {
  final int matchPct;
  final List<String> met;
  final List<String> missing;
  final String verdict;
  final bool ai;
  ResumeMatch(
      {required this.matchPct,
      required this.met,
      required this.missing,
      required this.verdict,
      this.ai = false});

  factory ResumeMatch.fromAi(Map<String, dynamic> d) {
    final reqs = (d['requirements'] as List?) ?? const [];
    final met = <String>[], missing = <String>[];
    for (final r in reqs) {
      final m = Map<String, dynamic>.from(r as Map);
      final status = '${m['status']}';
      final label = '${m['label']}';
      if (status == 'met') {
        met.add(label);
      } else if (status == 'missing') {
        missing.add(label);
      }
    }
    return ResumeMatch(
      matchPct: (_int(d['match_pct'])).clamp(0, 100),
      met: met,
      missing: missing,
      verdict: '${d['verdict'] ?? ''}',
      ai: true,
    );
  }

  /// Keyword fallback when no Edge Function / key is available.
  factory ResumeMatch.keyword(Job job, String resume) {
    final r = resume.toLowerCase();
    final reqs = <String>[];
    final q = job.qualification;
    if (q.isNotEmpty) reqs.add(q);
    for (final kw in ['degree', 'diploma', 'experience', job.dept]) {
      if (kw.trim().isNotEmpty) reqs.add(kw);
    }
    final met = <String>[], missing = <String>[];
    for (final req in reqs.toSet()) {
      final tokens =
          req.toLowerCase().split(RegExp(r'[^a-z0-9]+')).where((t) => t.length > 2);
      final hit = tokens.isNotEmpty && tokens.any(r.contains);
      (hit ? met : missing).add(req);
    }
    final total = met.length + missing.length;
    final pct = total == 0 ? 0 : ((met.length / total) * 100).round();
    return ResumeMatch(
      matchPct: pct,
      met: met,
      missing: missing,
      verdict: total == 0
          ? 'Add your resume details to get a match.'
          : 'Keyword match — $pct% of requirements found in your resume.',
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Study plan (rule-based fallback; AI version comes from the Edge Function)
// ─────────────────────────────────────────────────────────────────────────────
class StudyPhase {
  final String name, duration, focus;
  final List<String> topics;
  StudyPhase(this.name, this.duration, this.focus, this.topics);
  factory StudyPhase.fromMap(Map m) => StudyPhase(
        '${m['name'] ?? ''}',
        '${m['duration'] ?? ''}',
        '${m['focus'] ?? ''}',
        ((m['topics'] as List?) ?? const []).map((e) => '$e').toList(),
      );
}

class StudyPlan {
  final String exam, overview;
  final int daysLeft;
  final bool ai;
  final List<StudyPhase> phases;
  final List<String> highPriority, dailyRoutine, freeResources, tips;
  StudyPlan({
    required this.exam,
    required this.overview,
    required this.daysLeft,
    required this.ai,
    required this.phases,
    required this.highPriority,
    required this.dailyRoutine,
    required this.freeResources,
    required this.tips,
  });

  static List<String> _strs(dynamic v) =>
      ((v as List?) ?? const []).map((e) => '$e').toList();

  factory StudyPlan.fromAi(Map<String, dynamic> d) => StudyPlan(
        exam: '${d['exam'] ?? 'Exam'}',
        overview: '${d['overview'] ?? ''}',
        daysLeft: _int(d['days_left']),
        ai: true,
        phases:
            ((d['phases'] as List?) ?? const []).map((e) => StudyPhase.fromMap(e as Map)).toList(),
        highPriority: _strs(d['high_priority_topics']),
        dailyRoutine: _strs(d['daily_routine']),
        freeResources: _strs(d['free_resources']),
        tips: _strs(d['tips']),
      );

  /// Rule-based, time-scaled plan (port of evaluator._fallback_study_plan).
  factory StudyPlan.fallback(String exam, int? days, int hours) {
    final d = (days != null && days > 0) ? days : 60;
    final f = (d * 0.40).round().clamp(1, d);
    final p = (d * 0.35).round().clamp(1, d);
    final r = (d - f - p).clamp(1, d);
    return StudyPlan(
      exam: exam,
      daysLeft: d,
      ai: false,
      overview:
          'You have roughly $d days at about ${hours}h/day. Split the time into '
          'foundation, intensive practice, and revision. Prioritise high-weight topics '
          'and current affairs, and take regular timed mock tests.',
      phases: [
        StudyPhase('Phase 1 — Foundation', 'first ~$f days',
            'Cover the full official syllabus & build concepts', [
          'Map the official syllabus & exam pattern',
          'Core subjects at NCERT level',
          'State GK (CG/UP): history, geography, polity, schemes',
        ]),
        StudyPhase('Phase 2 — Practice', 'next ~$p days',
            'Solve previous papers & sectional tests', [
          'Previous year question papers',
          'Sectional / topic-wise mock tests',
          'Current affairs (last 6–12 months)',
        ]),
        StudyPhase('Phase 3 — Revision', 'final ~$r days',
            'Full-length mocks, analysis & revision', [
          'One full-length mock daily + analysis',
          'Revise notes, formulas & GK',
          'Drill weak areas',
        ]),
      ],
      highPriority: const [
        'Official syllabus core topics',
        'State GK & current affairs',
        'General Studies / GK',
        'Quantitative aptitude & reasoning',
        'Language paper (Hindi/English) as per pattern',
      ],
      dailyRoutine: [
        '~${(hours - 1).clamp(1, 24)}h concept + practice on the day\'s topic',
        '~1h current affairs + GK',
        '20–30 MCQs daily with review',
      ],
      freeResources: const [
        'NCERT — subject basics (History, Polity, Geography)',
        'SWAYAM / NPTEL — deeper or technical topics',
        'PIB & Yojana — current affairs & government schemes',
        'National Digital Library — reference books & papers',
      ],
      tips: const [
        'Take at least one full-length mock every week and analyse mistakes',
        "Revise weekly — don't only consume new material",
        'Prioritise high-weight topics first',
        'Keep a daily current-affairs habit',
      ],
    );
  }
}
