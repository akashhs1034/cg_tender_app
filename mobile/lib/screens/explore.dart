import 'package:flutter/material.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';
import 'evaluator.dart';
import 'resume_analyzer.dart';

/// Unified discovery search across tenders + jobs in one place (the web app's
/// Explore tab). Type once, see matching opportunities of both kinds.
class ExploreScreen extends StatefulWidget {
  const ExploreScreen({super.key});
  @override
  State<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends State<ExploreScreen> {
  List<Tender> _tenders = [];
  List<Job> _jobs = [];
  Map<String, dynamic> _profile = {};
  bool _loading = true;
  String? _error;
  String _q = '';
  int _kind = 0; // 0 = all, 1 = tenders, 2 = jobs

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final r = await Future.wait([Data.tenders(), Data.jobs(), Data.profile()]);
      _tenders = r[0] as List<Tender>;
      _jobs = r[1] as List<Job>;
      _profile = r[2] as Map<String, dynamic>;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final q = _q.toLowerCase();
    final tenders = (_kind == 2 || q.isEmpty)
        ? <Tender>[]
        : _tenders
            .where((t) => '${t.title} ${t.org} ${t.district} ${t.sector}'
                .toLowerCase()
                .contains(q))
            .take(40)
            .toList();
    final jobs = (_kind == 1 || q.isEmpty)
        ? <Job>[]
        : _jobs
            .where((j) => '${j.title} ${j.dept} ${j.qualification}'
                .toLowerCase()
                .contains(q))
            .take(40)
            .toList();

    return Scaffold(
      appBar: AppBar(title: const Text('🔎 Explore')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? ErrorRetry(message: _error!, onRetry: _load)
              : ListView(
                  padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
                  children: [
                    TextField(
                      autofocus: true,
                      decoration: const InputDecoration(
                          hintText: 'Search tenders & jobs…',
                          prefixIcon: Icon(Icons.search, color: Brand.muted)),
                      onChanged: (v) => setState(() => _q = v),
                    ),
                    const SizedBox(height: 10),
                    SegmentedButton<int>(
                      segments: const [
                        ButtonSegment(value: 0, label: Text('All')),
                        ButtonSegment(value: 1, label: Text('Tenders')),
                        ButtonSegment(value: 2, label: Text('Jobs')),
                      ],
                      selected: {_kind},
                      showSelectedIcon: false,
                      onSelectionChanged: (s) => setState(() => _kind = s.first),
                    ),
                    const SizedBox(height: 12),
                    if (q.isEmpty)
                      const InfoBanner(
                          'Type to search across every tender and government job at once.'),
                    if (tenders.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text('📄 Tenders (${tenders.length})',
                          style: const TextStyle(
                              color: Brand.cyan, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 6),
                      ...tenders.map(_tenderRow),
                    ],
                    if (jobs.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text('💼 Jobs (${jobs.length})',
                          style: const TextStyle(
                              color: Brand.cyan, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 6),
                      ...jobs.map(_jobRow),
                    ],
                    if (q.isNotEmpty && tenders.isEmpty && jobs.isEmpty)
                      const Padding(
                        padding: EdgeInsets.only(top: 40),
                        child: Center(
                            child: Text('No matches — try a different term',
                                style: TextStyle(color: Brand.muted))),
                      ),
                  ],
                ),
    );
  }

  Widget _tenderRow(Tender t) {
    final verdict = Eligibility.verdict(t, _profile);
    return Card(
      child: ListTile(
        title: Text(t.title,
            style: const TextStyle(color: Brand.text, fontSize: 13),
            maxLines: 2,
            overflow: TextOverflow.ellipsis),
        subtitle: Text('🏛 ${t.org}  ·  💰 ${t.valueLabel}',
            style: const TextStyle(color: Brand.muted, fontSize: 11)),
        trailing: verdict == 'ELIGIBLE'
            ? const Icon(Icons.verified, color: Brand.green, size: 18)
            : const Icon(Icons.chevron_right, color: Brand.muted),
        onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
                builder: (_) => EvaluatorScreen(tender: t, profile: _profile))),
      ),
    );
  }

  Widget _jobRow(Job j) {
    return Card(
      child: ListTile(
        title: Text(j.title,
            style: const TextStyle(color: Brand.text, fontSize: 13),
            maxLines: 2,
            overflow: TextOverflow.ellipsis),
        subtitle: Text('🏛 ${j.dept}  ·  ${j.state}',
            style: const TextStyle(color: Brand.muted, fontSize: 11)),
        trailing: const Icon(Icons.fact_check_outlined, color: Brand.cyan, size: 18),
        onTap: () => Navigator.push(context,
            MaterialPageRoute(builder: (_) => ResumeAnalyzerScreen(job: j))),
      ),
    );
  }
}
