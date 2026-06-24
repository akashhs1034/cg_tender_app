import 'package:flutter/material.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';
import 'explore.dart';
import 'bid_workshop.dart';
import 'study_matrix.dart';
import 'portals_screen.dart';
import 'alerts.dart';
import 'evaluator.dart';

/// Home hub — greeting, urgent-alert summary, quick actions for every feature
/// not on the bottom bar, and a peek at the user's top eligible tenders.
class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  bool _loading = true;
  Map<String, dynamic> _profile = {};
  List<Tender> _tenders = [];
  int _alertCount = 0;
  List<Tender> _topEligible = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final r = await Future.wait([Data.tenders(), Data.profile(), Data.documents()]);
      _tenders = r[0] as List<Tender>;
      _profile = r[1] as Map<String, dynamic>;
      final docs = r[2] as List<Map<String, dynamic>>;

      final closing = _tenders.where((t) {
        final dl = t.daysLeft;
        return dl != null &&
            dl >= 0 &&
            dl <= 7 &&
            Eligibility.verdict(t, _profile) == 'ELIGIBLE';
      }).length;
      final expiring = docs.where((d) {
        final exp = DateTime.tryParse('${d['expiry_date'] ?? ''}');
        if (exp == null) return false;
        final days = exp.difference(DateTime.now()).inDays;
        return days <= 30;
      }).length;
      _alertCount = closing + expiring;

      _topEligible = _tenders
          .where((t) => Eligibility.verdict(t, _profile) == 'ELIGIBLE')
          .toList()
        ..sort((a, b) => (a.daysLeft ?? 999).compareTo(b.daysLeft ?? 999));
    } catch (_) {/* dashboard is best-effort */}
    if (mounted) setState(() => _loading = false);
  }

  void _go(Widget screen) =>
      Navigator.push(context, MaterialPageRoute(builder: (_) => screen));

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    final configured = Eligibility.profileConfigured(_profile);
    final name = '${_profile['company_name'] ?? ''}'.trim();

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
        children: [
          const Text('Opporta',
              style: TextStyle(
                  color: Brand.cyan, fontSize: 24, fontWeight: FontWeight.w900)),
          Text(name.isEmpty ? Data.email : 'Welcome, $name',
              style: const TextStyle(color: Brand.muted, fontSize: 12.5)),
          const SizedBox(height: 14),

          // Alert summary
          InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: () => _go(const AlertsScreen()),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: (_alertCount > 0 ? Brand.amber : Brand.green)
                    .withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                    color: (_alertCount > 0 ? Brand.amber : Brand.green)
                        .withValues(alpha: 0.3)),
              ),
              child: Row(children: [
                Text(_alertCount > 0 ? '🔔' : '✅', style: const TextStyle(fontSize: 22)),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _alertCount > 0
                        ? '$_alertCount things need your attention'
                        : 'You\'re all caught up',
                    style: TextStyle(
                        color: _alertCount > 0 ? Brand.amber : Brand.green,
                        fontWeight: FontWeight.w700),
                  ),
                ),
                const Icon(Icons.chevron_right, color: Brand.muted),
              ]),
            ),
          ),
          const SizedBox(height: 18),

          const Text('Quick actions',
              style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          GridView.count(
            crossAxisCount: 3,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 10,
            crossAxisSpacing: 10,
            childAspectRatio: 0.95,
            children: [
              _action('🔎', 'Explore', () => _go(const ExploreScreen())),
              _action('🛠', 'Bid Workshop', () => _go(const BidWorkshopScreen())),
              _action('🧭', 'Study Matrix', () => _go(const StudyMatrixScreen())),
              _action('🔔', 'Alerts', () => _go(const AlertsScreen())),
              _action('🌐', 'Portals', () => _go(const PortalsScreen())),
            ],
          ),

          if (!configured) ...[
            const SizedBox(height: 16),
            const InfoBanner(
                'ℹ️ Complete your profile so Opporta can flag which tenders you\'re eligible for and tailor your scores.'),
          ],

          if (_topEligible.isNotEmpty) ...[
            const SizedBox(height: 18),
            const Text('🎯 Your top eligible tenders',
                style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            ..._topEligible.take(5).map((t) => Card(
                  child: ListTile(
                    title: Text(t.title,
                        style: const TextStyle(color: Brand.text, fontSize: 13),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis),
                    subtitle: Text(
                        '🏛 ${t.org}  ·  ${t.daysLeft != null && t.daysLeft! >= 0 ? "⏱ ${t.daysLeft}d" : ""}',
                        style: const TextStyle(color: Brand.muted, fontSize: 11)),
                    trailing: const Icon(Icons.insights, color: Brand.cyan, size: 18),
                    onTap: () =>
                        _go(EvaluatorScreen(tender: t, profile: _profile)),
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _action(String emoji, String label, VoidCallback onTap) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Brand.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Brand.border),
        ),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Text(emoji, style: const TextStyle(fontSize: 24)),
          const SizedBox(height: 6),
          Text(label,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Brand.text, fontSize: 11.5)),
        ]),
      ),
    );
  }
}
