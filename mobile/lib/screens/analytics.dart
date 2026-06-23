import 'package:flutter/material.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});
  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  List<Tender> _tenders = [];
  List<Job> _jobs = [];
  bool _loading = true;
  String? _error;

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
      final r = await Future.wait([Data.tenders(), Data.jobs()]);
      _tenders = r[0] as List<Tender>;
      _jobs = r[1] as List<Job>;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorRetry(message: _error!, onRetry: _load);

    final cg = _tenders.where((t) => t.state == 'Chhattisgarh').length;
    final up = _tenders.where((t) => t.state == 'Uttar Pradesh').length;
    final bySector = <String, int>{};
    for (final t in _tenders) {
      bySector[t.sector] = (bySector[t.sector] ?? 0) + 1;
    }
    final sectors = bySector.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
        children: [
          const SectionTitle('📊 Analytics'),
          const SizedBox(height: 12),
          Row(children: [
            _stat('${_tenders.length}', 'Tenders'),
            const SizedBox(width: 10),
            _stat('${_jobs.length}', 'Jobs'),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            _stat('$cg', 'CG Tenders'),
            const SizedBox(width: 10),
            _stat('$up', 'UP Tenders'),
          ]),
          const SizedBox(height: 18),
          const Text('Tenders by sector',
              style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          ...sectors.map((e) => _bar(e.key, e.value, _tenders.length)),
        ],
      ),
    );
  }

  Widget _stat(String num, String label) => Expanded(
        child: Card(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 18),
            child: Column(children: [
              Text(num,
                  style: const TextStyle(
                      color: Brand.cyan, fontSize: 26, fontWeight: FontWeight.w900)),
              const SizedBox(height: 4),
              Text(label, style: const TextStyle(color: Brand.muted, fontSize: 12)),
            ]),
          ),
        ),
      );

  Widget _bar(String label, int n, int total) {
    final frac = total == 0 ? 0.0 : n / total;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Expanded(
              child: Text(label,
                  style: const TextStyle(color: Brand.text, fontSize: 12.5))),
          Text('$n', style: const TextStyle(color: Brand.muted, fontSize: 12)),
        ]),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(
            value: frac,
            minHeight: 7,
            backgroundColor: Brand.surface2,
            valueColor: const AlwaysStoppedAnimation(Brand.cyan),
          ),
        ),
      ]),
    );
  }
}
