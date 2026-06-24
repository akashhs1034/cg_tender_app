import 'package:flutter/material.dart';
import '../config.dart';
import '../data.dart';
import '../intelligence.dart';
import 'widgets.dart';
import 'profile_edit.dart';

/// Resume Analyzer — matches the signed-in user's job-seeker profile against a
/// specific posting. Uses the `intelligence` Edge Function (AI) when available,
/// else an on-device keyword match.
class ResumeAnalyzerScreen extends StatefulWidget {
  final Job job;
  const ResumeAnalyzerScreen({super.key, required this.job});
  @override
  State<ResumeAnalyzerScreen> createState() => _ResumeAnalyzerScreenState();
}

class _ResumeAnalyzerScreenState extends State<ResumeAnalyzerScreen> {
  bool _busy = true;
  ResumeMatch? _match;
  Map<String, dynamic> _profile = {};

  @override
  void initState() {
    super.initState();
    _run();
  }

  String _resumeText(Map<String, dynamic> p) {
    final parts = <String>[];
    for (final f in ['full_name', 'qualification', 'degree_type', 'job_category']) {
      final v = '${p[f] ?? ''}'.trim();
      if (v.isNotEmpty) parts.add(v);
    }
    for (final lst in ['job_skills', 'languages']) {
      if (p[lst] is List) parts.addAll((p[lst] as List).map((e) => '$e'));
    }
    final yrs = int.tryParse('${p['job_experience_years'] ?? 0}') ?? 0;
    if (yrs > 0) parts.add('$yrs years experience');
    return parts.join(' ');
  }

  Future<void> _run() async {
    setState(() => _busy = true);
    _profile = await Data.profile();
    final resume = _resumeText(_profile);
    if (resume.trim().isEmpty) {
      setState(() => _busy = false);
      return;
    }
    // Try AI first, fall back to keyword match.
    final ai = await Data.analyzeResume(job: widget.job.raw, resumeText: resume);
    if (ai.isNotEmpty && ai['requirements'] != null) {
      _match = ResumeMatch.fromAi(ai);
    } else {
      _match = ResumeMatch.keyword(widget.job, resume);
    }
    if (mounted) setState(() => _busy = false);
  }

  Color _c(int p) => p >= 75 ? Brand.green : (p >= 50 ? Brand.amber : Brand.red);

  @override
  Widget build(BuildContext context) {
    final j = widget.job;
    return Scaffold(
      appBar: AppBar(title: const Text('📄 Resume Analyzer')),
      body: _busy
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(j.title,
                    style: const TextStyle(
                        color: Brand.text, fontWeight: FontWeight.w800, fontSize: 16)),
                const SizedBox(height: 4),
                Text('🏛 ${j.dept}  ·  ${j.state}',
                    style: const TextStyle(color: Brand.muted, fontSize: 12)),
                if (j.qualification.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text('Required: ${j.qualification}',
                      style: const TextStyle(color: Brand.muted, fontSize: 12.5)),
                ],
                const SizedBox(height: 16),
                if (_match == null)
                  _noProfile()
                else
                  ..._result(_match!),
              ],
            ),
    );
  }

  Widget _noProfile() => Column(children: [
        const InfoBanner(
            'ℹ️ Add your job-seeker profile (degree, skills, experience) to see how well you match this posting.'),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: () async {
            await Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) => ProfileEditScreen(initial: _profile)));
            _run();
          },
          icon: const Icon(Icons.edit, size: 18),
          label: const Text('Complete job profile'),
        ),
      ]);

  List<Widget> _result(ResumeMatch m) {
    final c = _c(m.matchPct);
    return [
      Center(
        child: Column(children: [
          SizedBox(
            width: 96,
            height: 96,
            child: Stack(alignment: Alignment.center, children: [
              SizedBox(
                width: 96,
                height: 96,
                child: CircularProgressIndicator(
                  value: m.matchPct / 100,
                  strokeWidth: 8,
                  backgroundColor: Brand.surface2,
                  valueColor: AlwaysStoppedAnimation(c),
                ),
              ),
              Text('${m.matchPct}%',
                  style: TextStyle(color: c, fontSize: 24, fontWeight: FontWeight.w900)),
            ]),
          ),
          const SizedBox(height: 8),
          Text(m.ai ? '⚡ Opporta Intelligence' : '📋 Keyword match',
              style: const TextStyle(color: Brand.muted, fontSize: 11)),
        ]),
      ),
      const SizedBox(height: 16),
      if (m.verdict.isNotEmpty) InfoBanner(m.verdict),
      if (m.met.isNotEmpty) ...[
        const SizedBox(height: 14),
        const Text('✅ You meet',
            style: TextStyle(color: Brand.green, fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
        ...m.met.map((r) => _line(r, Brand.green)),
      ],
      if (m.missing.isNotEmpty) ...[
        const SizedBox(height: 14),
        const Text('⚠ Gaps to address',
            style: TextStyle(color: Brand.red, fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
        ...m.missing.map((r) => _line(r, Brand.red)),
      ],
      const SizedBox(height: 16),
      const Text(
        'Automated screening estimate — not an official eligibility decision. '
        "Always confirm criteria on the recruitment authority's portal.",
        style: TextStyle(color: Brand.muted, fontSize: 11, height: 1.5),
      ),
    ];
  }

  Widget _line(String t, Color c) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(c == Brand.green ? Icons.check_circle : Icons.error_outline,
              size: 15, color: c),
          const SizedBox(width: 8),
          Expanded(
              child: Text(t,
                  style: const TextStyle(color: Brand.text, fontSize: 12.5, height: 1.3))),
        ]),
      );
}
