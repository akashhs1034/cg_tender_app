import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';

/// "🔔 For you" — the in-app smart-alert feed (mirrors the web app's
/// compute_smart_alerts): eligible tenders closing soon + documents expiring
/// soon. This is the on-screen companion to the push notifications.
class AlertItem {
  final String icon, title, subtitle, url;
  final Color color;
  AlertItem(this.icon, this.title, this.subtitle, this.color, [this.url = '']);
}

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});
  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  bool _loading = true;
  String? _error;
  List<AlertItem> _items = [];

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
      final r = await Future.wait([Data.tenders(), Data.profile(), Data.documents()]);
      final tenders = r[0] as List<Tender>;
      final profile = r[1] as Map<String, dynamic>;
      final docs = r[2] as List<Map<String, dynamic>>;
      _items = _compute(tenders, profile, docs);
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<AlertItem> _compute(
      List<Tender> tenders, Map<String, dynamic> profile, List<Map<String, dynamic>> docs) {
    final out = <AlertItem>[];

    // 1) Eligible tenders closing within 7 days.
    final closing = tenders.where((t) {
      final dl = t.daysLeft;
      return dl != null &&
          dl >= 0 &&
          dl <= 7 &&
          Eligibility.verdict(t, profile) == 'ELIGIBLE';
    }).toList()
      ..sort((a, b) => (a.daysLeft ?? 99).compareTo(b.daysLeft ?? 99));
    for (final t in closing.take(20)) {
      out.add(AlertItem('⏱', t.title,
          'Eligible · closes in ${t.daysLeft}d · ${t.org}', Brand.amber, t.url));
    }

    // 2) Documents expiring within 30 days.
    for (final d in docs) {
      final exp = DateTime.tryParse('${d['expiry_date'] ?? ''}');
      if (exp == null) continue;
      final days = exp.difference(DateTime.now()).inDays;
      if (days < 0) {
        out.add(AlertItem('⛔', '${d['name'] ?? d['filename'] ?? 'Document'}',
            'Expired ${-days}d ago — renew to stay eligible', Brand.red));
      } else if (days <= 30) {
        out.add(AlertItem('📄', '${d['name'] ?? d['filename'] ?? 'Document'}',
            'Expires in ${days}d — renew to stay eligible', Brand.amber));
      }
    }

    return out;
  }

  Future<void> _open(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null && url.startsWith('http')) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🔔 For You')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? ErrorRetry(message: _error!, onRetry: _load)
              : RefreshIndicator(
                  onRefresh: _load,
                  child: _items.isEmpty
                      ? ListView(children: const [
                          SizedBox(height: 120),
                          Icon(Icons.notifications_off_outlined,
                              size: 48, color: Brand.muted),
                          SizedBox(height: 12),
                          Center(
                              child: Text('No urgent alerts right now',
                                  style: TextStyle(color: Brand.muted))),
                          SizedBox(height: 6),
                          Center(
                              child: Text(
                                  'Eligible tenders closing soon and expiring documents show up here.',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(color: Brand.muted, fontSize: 12))),
                        ])
                      : ListView(
                          padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
                          children: [
                            Text('${_items.length} things need your attention',
                                style: const TextStyle(color: Brand.muted, fontSize: 12)),
                            const SizedBox(height: 8),
                            ..._items.map((a) => Card(
                                  child: ListTile(
                                    leading: Text(a.icon,
                                        style: const TextStyle(fontSize: 20)),
                                    title: Text(a.title,
                                        style: const TextStyle(
                                            color: Brand.text, fontSize: 13.5),
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis),
                                    subtitle: Text(a.subtitle,
                                        style: TextStyle(color: a.color, fontSize: 11.5)),
                                    trailing: a.url.isNotEmpty
                                        ? const Icon(Icons.open_in_new,
                                            size: 16, color: Brand.cyan)
                                        : null,
                                    onTap: a.url.isNotEmpty ? () => _open(a.url) : null,
                                  ),
                                )),
                          ],
                        ),
                ),
    );
  }
}
