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
  Map<String, dynamic> _profile = {};
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
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorRetry(message: _error!, onRetry: _load);

    final cg = _tenders.where((t) => t.state == 'Chhattisgarh').length;
    final up = _tenders.where((t) => t.state == 'Uttar Pradesh').length;
    final configured = Eligibility.profileConfigured(_profile);
    final eligible = configured
        ? _tenders.where((t) => Eligibility.verdict(t, _profile) == 'ELIGIBLE').length
        : 0;
    final closingWeek = _tenders.where((t) {
      final dl = t.daysLeft;
      return dl != null && dl >= 0 && dl <= 7;
    }).length;
    final totalValue = _tenders.fold<double>(0, (s, t) => s + t.valueLakhs);

    final bySector = <String, int>{};
    for (final t in _tenders) {
      bySector[t.sector] = (bySector[t.sector] ?? 0) + 1;
    }
    final sectors = bySector.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    final byDistrict = <String, int>{};
    for (final t in _tenders) {
      if (t.district.isEmpty || t.district == 'State-wide') continue;
      byDistrict[t.district] = (byDistrict[t.district] ?? 0) + 1;
    }
    final districts = byDistrict.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    final jobsCg = _jobs.where((j) => j.state == 'Chhattisgarh').length;
    final jobsUp = _jobs.where((j) => j.state == 'Uttar Pradesh').length;

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
        children: [
          const SectionTitle('📊 Analytics'),
          const SizedBox(height: 12),
          Row(children: [
            _stat('${_tenders.length}', 'Tenders', Brand.cyan),
            const SizedBox(width: 10),
            _stat('${_jobs.length}', 'Jobs', Brand.cyan),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            _stat('$cg', 'CG Tenders', Brand.blue),
            const SizedBox(width: 10),
            _stat('$up', 'UP Tenders', Brand.blue),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            if (configured)
              _stat('$eligible', 'Eligible', Brand.green)
            else
              _stat('—', 'Eligible', Brand.muted),
            const SizedBox(width: 10),
            _stat('$closingWeek', 'Closing ≤7d', Brand.amber),
          ]),
          const SizedBox(height: 14),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(children: [
                const Icon(Icons.account_balance_wallet_outlined, color: Brand.cyan),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('Total pipeline value',
                        style: TextStyle(color: Brand.muted, fontSize: 12)),
                    const SizedBox(height: 2),
                    Text(_money(totalValue),
                        style: const TextStyle(
                            color: Brand.text, fontSize: 18, fontWeight: FontWeight.w800)),
                  ]),
                ),
              ]),
            ),
          ),
          if (!configured)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: InfoBanner(
                  'ℹ️ Complete your contractor profile to see how many tenders you are eligible for.'),
            ),
          const SizedBox(height: 18),
          const Text('Tenders by sector',
              style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          ...sectors.take(12).map((e) => _bar(e.key, e.value, _tenders.length)),
          if (districts.isNotEmpty) ...[
            const SizedBox(height: 18),
            const Text('Top districts',
                style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            ...districts.take(8).map((e) => _bar(e.key, e.value, _tenders.length)),
          ],
          const SizedBox(height: 18),
          const Text('Jobs by state',
              style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          _bar('Chhattisgarh', jobsCg, _jobs.length),
          _bar('Uttar Pradesh', jobsUp, _jobs.length),
        ],
      ),
    );
  }

  String _money(double lakhs) {
    if (lakhs >= 100) return '₹${(lakhs / 100).toStringAsFixed(1)} Cr';
    return '₹${lakhs.toStringAsFixed(0)} L';
  }

  Widget _stat(String num, String label, Color color) => Expanded(
        child: Card(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 18),
            child: Column(children: [
              Text(num,
                  style: TextStyle(
                      color: color, fontSize: 26, fontWeight: FontWeight.w900)),
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
                  style: const TextStyle(color: Brand.text, fontSize: 12.5),
                  overflow: TextOverflow.ellipsis)),
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
