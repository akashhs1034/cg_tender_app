import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';
import 'bid_workshop.dart';

class TendersScreen extends StatefulWidget {
  const TendersScreen({super.key});
  @override
  State<TendersScreen> createState() => _TendersScreenState();
}

class _TendersScreenState extends State<TendersScreen> {
  List<Tender> _all = [];
  List<Tender> _offline = [];
  Map<String, dynamic> _profile = {};
  bool _loading = true;
  String? _error;

  bool _showOffline = false;
  String _q = '';
  String _state = 'All';
  String _sector = 'All';

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
      final results = await Future.wait(
          [Data.tenders(), Data.profile(), Data.offlineTenders()]);
      _all = results[0] as List<Tender>;
      _profile = results[1] as Map<String, dynamic>;
      _offline = results[2] as List<Tender>;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<Tender> get _filtered {
    final q = _q.toLowerCase();
    final src = _showOffline ? _offline : _all;
    final out = src.where((t) {
      if (q.isNotEmpty &&
          !('${t.title} ${t.org} ${t.district}'.toLowerCase().contains(q))) {
        return false;
      }
      if (_state != 'All' && t.state != _state) return false;
      if (!_showOffline && _sector != 'All' && t.sector != _sector) return false;
      return true;
    }).toList();
    if (!_showOffline) {
      // Eligible tenders first.
      out.sort((a, b) {
        int rank(Tender t) =>
            Eligibility.verdict(t, _profile) == 'ELIGIBLE' ? 1 : 0;
        return rank(b).compareTo(rank(a));
      });
    }
    return out;
  }

  List<String> get _sectors {
    final s = _all.map((t) => t.sector).toSet().toList()..sort();
    return ['All', ...s];
  }

  Future<void> _open(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null && url.startsWith('http')) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return ErrorRetry(message: _error!, onRetry: _load);
    }
    final rows = _filtered;
    final configured = Eligibility.profileConfigured(_profile);

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
        children: [
          const SectionTitle('📄 Tender Portal'),
          const SizedBox(height: 10),
          FilledButton.icon(
            onPressed: () => Navigator.push(context,
                MaterialPageRoute(builder: (_) => const BidWorkshopScreen())),
            icon: const Icon(Icons.build, size: 18),
            label: const Text('🛠  Bid Workshop — draft a ready-to-bid file'),
            style: FilledButton.styleFrom(
                backgroundColor: Brand.green,
                foregroundColor: const Color(0xFF02040A)),
          ),
          const SizedBox(height: 12),
          SegmentedButton<bool>(
            segments: const [
              ButtonSegment(
                  value: false,
                  label: Text('Online'),
                  icon: Icon(Icons.public, size: 15)),
              ButtonSegment(
                  value: true,
                  label: Text('Newspaper'),
                  icon: Icon(Icons.newspaper, size: 15)),
            ],
            selected: {_showOffline},
            showSelectedIcon: false,
            onSelectionChanged: (s) => setState(() => _showOffline = s.first),
          ),
          const SizedBox(height: 10),
          TextField(
            decoration: const InputDecoration(
                hintText: 'Search title, org, district…',
                prefixIcon: Icon(Icons.search, color: Brand.muted)),
            onChanged: (v) => setState(() => _q = v),
          ),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
                child: _dropdown('State', _state,
                    ['All', 'Chhattisgarh', 'Uttar Pradesh'],
                    (v) => setState(() => _state = v))),
            const SizedBox(width: 10),
            Expanded(
                child: _dropdown('Sector', _sector, _sectors,
                    (v) => setState(() => _sector = v))),
          ]),
          const SizedBox(height: 10),
          if (!configured && !_showOffline)
            const InfoBanner(
                '🔒 Complete your profile (class, turnover, experience) to see which tenders you are eligible for.'),
          if (_showOffline)
            const InfoBanner(
                '🗞 Government tenders advertised in CG/UP newspapers (via Samvad + district sites). Tap to view the official notice.'),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Text('${rows.length} ${_showOffline ? "newspaper " : ""}tenders',
                style: const TextStyle(color: Brand.muted, fontSize: 12)),
          ),
          ...rows.take(120).map((t) => _showOffline ? _offlineCard(t) : _card(t)),
        ],
      ),
    );
  }

  Widget _card(Tender t) {
    final verdict = Eligibility.verdict(t, _profile);
    final dl = t.daysLeft;
    final dlTxt = dl == null
        ? 'No deadline'
        : (dl < 0 ? '⚠ Expired' : '⏱ ${dl}d left');
    return Card(
      child: InkWell(
        onTap: t.url.isNotEmpty ? () => _open(t.url) : null,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(t.title,
                        style: const TextStyle(
                            color: Brand.text,
                            fontWeight: FontWeight.w700,
                            height: 1.3)),
                  ),
                  if (t.url.isNotEmpty)
                    const Icon(Icons.open_in_new, size: 16, color: Brand.cyan),
                ],
              ),
              const SizedBox(height: 6),
              Text('🏛 ${t.org}  ·  ${t.state}',
                  style: const TextStyle(color: Brand.muted, fontSize: 12)),
              const SizedBox(height: 10),
              Wrap(spacing: 6, runSpacing: 6, children: [
                Chip2('💰 ${t.valueLabel}'),
                Chip2(dlTxt),
                Chip2('📍 ${t.district}'),
                Chip2(t.sector),
                if (verdict == 'ELIGIBLE')
                  const Chip2('✅ Eligible', color: Brand.green),
                if (verdict == 'NOT ELIGIBLE')
                  const Chip2('❌ Not Eligible', color: Brand.red),
                if (verdict == null)
                  const Chip2('🔒 Check eligibility', color: Brand.muted),
              ]),
            ],
          ),
        ),
      ),
    );
  }

  Widget _offlineCard(Tender t) {
    return Card(
      child: InkWell(
        onTap: t.url.isNotEmpty ? () => _open(t.url) : null,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Expanded(
                  child: Text('📰 ${t.title}',
                      style: const TextStyle(
                          color: Brand.text,
                          fontWeight: FontWeight.w700,
                          height: 1.3)),
                ),
                if (t.url.isNotEmpty)
                  const Icon(Icons.open_in_new, size: 16, color: Brand.cyan),
              ]),
              const SizedBox(height: 6),
              Text('🏛 ${t.org}  ·  📍 ${t.district}',
                  style: const TextStyle(color: Brand.muted, fontSize: 12)),
              const SizedBox(height: 10),
              Wrap(spacing: 6, runSpacing: 6, children: [
                if (t.newspaper.isNotEmpty)
                  Chip2('🗞 ${t.newspaper}', color: Brand.cyan),
                if (t.deadline.isNotEmpty) Chip2('⏱ ${t.deadline}'),
                Chip2('📍 ${t.state}'),
              ]),
            ],
          ),
        ),
      ),
    );
  }

  Widget _dropdown(
      String label, String value, List<String> opts, ValueChanged<String> onCh) {
    return InputDecorator(
      decoration: InputDecoration(
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
          labelText: label,
          labelStyle: const TextStyle(color: Brand.muted, fontSize: 12)),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: opts.contains(value) ? value : opts.first,
          isExpanded: true,
          dropdownColor: Brand.surface,
          style: const TextStyle(color: Brand.text, fontSize: 13),
          items: opts
              .map((o) => DropdownMenuItem(value: o, child: Text(o, overflow: TextOverflow.ellipsis)))
              .toList(),
          onChanged: (v) => onCh(v ?? 'All'),
        ),
      ),
    );
  }
}
