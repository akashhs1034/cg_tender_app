import 'dart:math';
import 'dart:typed_data';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Thin data layer over the SAME Supabase backend the web app uses.
/// Public-read tables (tenders/jobs/offline_tenders/corrigendums) need no auth;
/// profiles/documents are protected by RLS and require the signed-in session.
class Data {
  static SupabaseClient get _sb => Supabase.instance.client;

  // ── Auth ──────────────────────────────────────────────────────────────────
  static User? get user => _sb.auth.currentUser;
  static bool get signedIn => _sb.auth.currentSession != null;
  static String get email => _sb.auth.currentUser?.email ?? '';

  static Future<void> signIn(String e, String p) =>
      _sb.auth.signInWithPassword(email: e.trim(), password: p);

  static Future<void> signUp(String e, String p) =>
      _sb.auth.signUp(email: e.trim(), password: p);

  static Future<void> signOut() => _sb.auth.signOut();

  // ── Reads ─────────────────────────────────────────────────────────────────
  static Future<List<Map<String, dynamic>>> _table(String name,
      {int limit = 1500}) async {
    final rows = await _sb.from(name).select().order('source_id').limit(limit);
    return (rows as List).cast<Map<String, dynamic>>();
  }

  static Future<List<Tender>> tenders() async =>
      (await _table('tenders')).map(Tender.fromMap).toList();

  static Future<List<Tender>> offlineTenders() async =>
      (await _table('offline_tenders')).map(Tender.fromMap).toList();

  static Future<List<Job>> jobs() async =>
      (await _table('jobs')).map(Job.fromMap).toList();

  /// The signed-in user's contractor profile (RLS-scoped). Empty if none.
  static Future<Map<String, dynamic>> profile() async {
    if (!signedIn) return {};
    try {
      final r = await _sb
          .from('profiles')
          .select()
          .eq('email', email)
          .maybeSingle();
      return r ?? {};
    } catch (_) {
      return {};
    }
  }

  static Future<List<Map<String, dynamic>>> documents() async {
    if (!signedIn) return [];
    try {
      final r = await _sb
          .from('documents')
          .select()
          .eq('email', email)
          .order('uploaded_at', ascending: false);
      return (r as List).cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }

  // ── Writes (RLS-scoped to the signed-in user) ───────────────────────────────
  /// Upsert the contractor profile. Only the given fields are written.
  static Future<void> saveProfile(Map<String, dynamic> fields) async {
    final row = <String, dynamic>{...fields, 'email': email};
    await _sb.from('profiles').upsert(row, onConflict: 'email');
  }

  /// Upload a document to the `vault` storage bucket + insert its metadata row.
  /// expiryDate is ISO 'YYYY-MM-DD' (drives renewal alerts on the web app).
  static Future<void> uploadDocument({
    required String name,
    required String filename,
    required Uint8List bytes,
    required String mimeType,
    String? expiryDate,
    String? docType,
  }) async {
    final docId = _randId();
    final path = '$email/$docId/$filename';
    await _sb.storage.from('vault').uploadBinary(
          path,
          bytes,
          fileOptions: FileOptions(contentType: mimeType, upsert: true),
        );
    await _sb.from('documents').insert({
      'doc_id': docId,
      'email': email,
      'name': name,
      'filename': filename,
      'mime_type': mimeType,
      'size_bytes': bytes.length,
      'uploaded_at': DateTime.now().toUtc().toIso8601String(),
      'expiry_date': expiryDate,
      'doc_type': docType,
    });
  }

  static String _randId() {
    final r = Random();
    return List.generate(16, (_) => r.nextInt(16).toRadixString(16)).join();
  }

  /// Call the bid-engine Edge Function (Gemini key stays server-side).
  /// Returns {tender:{...}, cover_letter, compliance:[...], manual_actions:[...]}
  /// or {error: ...}. Never throws.
  static Future<Map<String, dynamic>> draftBid({
    required String docBase64,
    required String mimeType,
    required Map<String, dynamic> profile,
  }) async {
    try {
      final res = await _sb.functions.invoke('bid-engine', body: {
        'docBase64': docBase64,
        'mimeType': mimeType,
        'profile': profile,
      });
      final d = res.data;
      if (d is Map) return Map<String, dynamic>.from(d);
      return {'error': 'unexpected response'};
    } catch (e) {
      return {'error': '$e'};
    }
  }

  // ── Corrigendums (public read) ──────────────────────────────────────────────
  static Future<List<Corrigendum>> corrigendums() async {
    try {
      final rows = await _sb
          .from('corrigendums')
          .select()
          .order('published_date', ascending: false)
          .limit(200);
      return (rows as List)
          .cast<Map<String, dynamic>>()
          .map(Corrigendum.fromMap)
          .toList();
    } catch (_) {
      return [];
    }
  }

  // ── Saved tenders / pipeline (RLS-scoped) ───────────────────────────────────
  static Future<Set<String>> savedTenderIds() async {
    if (!signedIn) return {};
    try {
      final r = await _sb.from('saved_tenders').select('source_id').eq('email', email);
      return (r as List).map((e) => '${e['source_id']}').toSet();
    } catch (_) {
      return {};
    }
  }

  static Future<List<Map<String, dynamic>>> savedTenders() async {
    if (!signedIn) return [];
    try {
      final r = await _sb
          .from('saved_tenders')
          .select()
          .eq('email', email)
          .order('saved_at', ascending: false);
      return (r as List).cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }

  static Future<void> saveTender(String sourceId, {String status = 'interested'}) async {
    await _sb.from('saved_tenders').upsert(
      {'email': email, 'source_id': sourceId, 'status': status},
      onConflict: 'email,source_id',
    );
  }

  static Future<void> unsaveTender(String sourceId) async {
    await _sb.from('saved_tenders').delete().match({'email': email, 'source_id': sourceId});
  }

  // ── Offline / newspaper tender capture (public insert policy) ───────────────
  static Future<int> saveOfflineTenders(List<Map<String, dynamic>> records) async {
    if (records.isEmpty) return 0;
    await _sb.from('offline_tenders').upsert(records, onConflict: 'source_id');
    return records.length;
  }

  // ── Document vault extras ───────────────────────────────────────────────────
  /// A time-limited download/preview URL for a vault document.
  static Future<String?> documentUrl(Map<String, dynamic> doc) async {
    final path = '$email/${doc['doc_id']}/${doc['filename']}';
    try {
      return await _sb.storage.from('vault').createSignedUrl(path, 60 * 60);
    } catch (_) {
      return null;
    }
  }

  static Future<void> deleteDocument(Map<String, dynamic> doc) async {
    final path = '$email/${doc['doc_id']}/${doc['filename']}';
    try {
      await _sb.storage.from('vault').remove([path]);
    } catch (_) {/* metadata removal below is what matters most */}
    await _sb.from('documents').delete().match({'email': email, 'doc_id': doc['doc_id']});
  }

  // ── Opporta Intelligence Edge Function (resume match + study plan) ───────────
  /// Calls the `intelligence` Edge Function. Returns {} on any failure so callers
  /// can fall back to the on-device rule-based version. Never throws.
  static Future<Map<String, dynamic>> _intelligence(Map<String, dynamic> body) async {
    try {
      final res = await _sb.functions.invoke('intelligence', body: body);
      final d = res.data;
      if (d is Map) return Map<String, dynamic>.from(d);
      return {};
    } catch (_) {
      return {};
    }
  }

  static Future<Map<String, dynamic>> analyzeResume({
    required Map<String, dynamic> job,
    required String resumeText,
  }) =>
      _intelligence({'task': 'resume', 'job': job, 'resume': resumeText});

  static Future<Map<String, dynamic>> studyPlan({
    required String exam,
    String examDate = '',
    int hours = 4,
  }) =>
      _intelligence(
          {'task': 'study_plan', 'exam': exam, 'exam_date': examDate, 'hours': hours});
}

// ─────────────────────────────────────────────────────────────────────────────
// Models
// ─────────────────────────────────────────────────────────────────────────────
String _s(dynamic v, [String d = '']) =>
    (v == null || '$v'.trim().isEmpty || '$v' == 'null') ? d : '$v'.trim();

double _d(dynamic v) {
  if (v == null) return 0;
  return double.tryParse('$v'.replaceAll(',', '')) ?? 0;
}

class Tender {
  final Map<String, dynamic> raw;
  Tender(this.raw);
  factory Tender.fromMap(Map<String, dynamic> m) => Tender(m);

  String get title => _s(raw['title'], 'Untitled tender');
  String get org => _s(raw['organization'], '—');
  String get state => _s(raw['state']);
  String get district => _s(raw['district'], 'State-wide');
  String get category => _s(raw['category'], 'General');
  String get valueText => _s(raw['value_text']);
  double get valueLakhs => _d(raw['value_lakhs']);
  String get contractorClass => _s(raw['contractor_class']);
  String get deadline => _s(raw['deadline']);
  String get url => _s(raw['document_url']);
  String get newspaper => _s(raw['newspaper']);
  String get sector => Eligibility.sector(title, org, category);

  String get valueLabel => valueText.isNotEmpty
      ? valueText
      : (valueLakhs > 0 ? '₹${valueLakhs.toStringAsFixed(0)}L' : '—');

  int? get daysLeft {
    final d = DateTime.tryParse(deadline);
    if (d == null) return null;
    return d.difference(DateTime.now()).inDays;
  }
}

class Job {
  final Map<String, dynamic> raw;
  Job(this.raw);
  factory Job.fromMap(Map<String, dynamic> m) => Job(m);

  String get title => _s(raw['title'], 'Government job');
  String get dept => _s(raw['department'], _s(raw['organization'], '—'));
  String get state => _s(raw['state']);
  String get category => _s(raw['category'], 'General');
  String get qualification => _s(raw['qualification']);
  String get vacancies => _s(raw['vacancies']);
  String get deadline => _s(raw['deadline']);
  String get description => _s(raw['description']);
  String get url => _s(raw['document_url'], _s(raw['apply_link'], _s(raw['source_url'])));

  int? get daysLeft {
    final d = DateTime.tryParse(deadline);
    if (d == null) return null;
    return d.difference(DateTime.now()).inDays;
  }
}

class Corrigendum {
  final Map<String, dynamic> raw;
  Corrigendum(this.raw);
  factory Corrigendum.fromMap(Map<String, dynamic> m) => Corrigendum(m);

  String get title => _s(raw['title'], 'Tender amendment');
  String get state => _s(raw['state']);
  String get closingDate => _s(raw['closing_date']);
  String get publishedDate => _s(raw['published_date']);
  String get corrigendumUrl => _s(raw['corrigendum_url']);
  String get tenderUrl => _s(raw['tender_url']);
}

// ─────────────────────────────────────────────────────────────────────────────
// Eligibility + sector — Dart port of the web app's binary gate (core.py /
// vault_evaluator.py). No percentage — just ELIGIBLE / NOT ELIGIBLE / null.
// ─────────────────────────────────────────────────────────────────────────────
class Eligibility {
  static const _classRank = {
    'open': 0, 'unlimited': 5,
    'class a': 4, 'a': 4, 'class b': 3, 'b': 3,
    'class c': 2, 'c': 2, 'class d': 1, 'd': 1, 'class e': 1, 'e': 1,
  };

  static int _rank(String? label) =>
      _classRank[(label ?? '').trim().toLowerCase()] ?? 0;

  /// 'ELIGIBLE' / 'NOT ELIGIBLE' / null (profile not configured).
  static String? verdict(Tender t, Map<String, dynamic> profile) {
    final myClass = _s(profile['contractor_class']);
    final myTurnover = _d(profile['turnover_lakhs']);
    final myExp = _d(profile['experience_years']).toInt();
    final configured = myClass.isNotEmpty || myTurnover > 0;
    if (!configured) return null;

    final reqClass = t.contractorClass;
    if (reqClass.isNotEmpty && _rank(reqClass) > 0 && _rank(myClass) > 0) {
      if (_rank(myClass) < _rank(reqClass)) return 'NOT ELIGIBLE';
    }
    final reqTurnover = t.valueLakhs > 0 ? t.valueLakhs * 0.3 : 0;
    if (reqTurnover > 0 && myTurnover > 0 && myTurnover < reqTurnover) {
      return 'NOT ELIGIBLE';
    }
    final reqExp = _d(t.raw['required_experience_years']).toInt();
    if (reqExp > 0 && myExp > 0 && myExp < reqExp) return 'NOT ELIGIBLE';
    return 'ELIGIBLE';
  }

  static bool profileConfigured(Map<String, dynamic> p) =>
      _s(p['contractor_class']).isNotEmpty || _d(p['turnover_lakhs']) > 0;

  // Lightweight sector classifier (title/org first, like core.classify_sector).
  static const _overrides = <String, List<String>>{
    'Police & Security': ['police', 'jail', 'prison', 'forensic', 'home guard'],
    'Government & Administration': [
      'collectorate', 'tehsil', 'revenue department', 'janpad', 'zila panchayat',
      'sachivalaya', 'mantralaya', 'vidhan sabha', 'district administration'],
    'Printing & Advertising': ['printing', 'advertis', 'publicity', 'jansampark',
      'samvad', 'hoarding'],
    'Water & Irrigation': ['water', 'irrigation', 'pipe', 'canal', 'drainage', 'sewer'],
    'Electrical & Energy': ['electric', 'solar', 'power', 'transformer', 'lighting'],
    'Medical & Healthcare': ['medical', 'health', 'hospital', 'surgical', 'pharma'],
    'Municipal Projects': ['municipal', 'nagar', 'sanitation', 'solid waste'],
    'Transport & Logistics': ['transport', 'vehicle', 'crane', 'coal', 'mining'],
    'Civil & Construction': ['civil', 'construction', 'road', 'bridge', 'building', 'rcc'],
  };

  static String sector(String title, String org, String category) {
    final blob = '$title $org $category'.toLowerCase();
    for (final e in _overrides.entries) {
      if (e.value.any(blob.contains)) return e.key;
    }
    return category.isEmpty ? 'Miscellaneous' : category;
  }
}
