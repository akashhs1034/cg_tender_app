import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';
import 'bid_workshop.dart';
import 'evaluator.dart';
import 'portals_screen.dart';

class TendersScreen extends StatefulWidget {
  const TendersScreen({super.key});
  @override
  State<TendersScreen> createState() => _TendersScreenState();
}

class _TendersScreenState extends State<TendersScreen> {
  List<Tender> _all = [];
  List<Tender> _offline = [];
  List<Corrigendum> _corrigendums = [];
  Map<String, dynamic> _profile = {};
  Set<String> _saved = {};
  bool _loading = true;
  String? _error;

  bool _showOffline = false;
  String _q = '';
  String _state = 'All';
  String _sector = 'All';
  String _district = 'All';

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
      final results = await Future.wait([
        Data.tenders(),
        Data.profile(),
        Data.offlineTenders(),
        Data.corrigendums(),
        Data.savedTenderIds(),
      ]);
      _all = results[0] as List<Tender>;
      _profile = results[1] as Map<String, dynamic>;
      _offline = results[2] as List<Tender>;
      _corrigendums = results[3] as List<Corrigendum>;
      _saved = results[4] as Set<String>;
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
      if (_district != 'All' && t.district != _district) return false;
      if (!_showOffline && _sector != 'All' && t.sector != _sector) return false;
      return true;
    }).toList();
    if (!_showOffline) {
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

  // Districts cascade from the chosen state (and the active online/offline set).
  List<String> get _districts {
    final src = _showOffline ? _offline : _all;
    final s = src
        .where((t) => _state == 'All' || t.state == _state)
        .map((t) => t.district)
        .where((d) => d.isNotEmpty && d != 'State-wide')
        .toSet()
        .toList()
      ..sort();
    return ['All', ...s];
  }

  Future<void> _open(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null && url.startsWith('http')) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _toggleSave(Tender t) async {
    final id = '${t.raw['source_id'] ?? ''}';
    if (id.isEmpty) return;
    if (!Data.signedIn) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Sign in to save tenders')));
      return;
    }
    final wasSaved = _saved.contains(id);
    setState(() => wasSaved ? _saved.remove(id) : _saved.add(id));
    try {
      wasSaved ? await Data.unsaveTender(id) : await Data.saveTender(id);
    } catch (_) {
      if (mounted) setState(() => wasSaved ? _saved.add(id) : _saved.remove(id));
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
          Row(children: [
            const Expanded(child: SectionTitle('📄 Tender Portal')),
            IconButton(
              tooltip: 'Official portals',
              icon: const Icon(Icons.public, color: Brand.cyan),
              onPressed: () => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const PortalsScreen())),
            ),
          ]),
          const SizedBox(height: 6),
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

          if (_corrigendums.isNotEmpty) _corrigendumsTile(),

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
            onSelectionChanged: (s) => setState(() {
              _showOffline = s.first;
              _district = 'All';
            }),
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
                    ['All', 'Chhattisgarh', 'Uttar Pradesh'], (v) {
              setState(() {
                _state = v;
                _district = 'All';
              });
            })),
            const SizedBox(width: 10),
            Expanded(
                child: _dropdown('District', _district, _districts,
                    (v) => setState(() => _district = v))),
          ]),
          if (!_showOffline) ...[
            const SizedBox(height: 10),
            _dropdown('Sector', _sector, _sectors,
                (v) => setState(() => _sector = v)),
          ],
          const SizedBox(height: 10),
          if (_showOffline)
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: _captureOffline,
                icon: const Icon(Icons.add, size: 18, color: Brand.cyan),
                label: const Text('Add a newspaper tender',
                    style: TextStyle(color: Brand.cyan)),
              ),
            ),
          if (!configured && !_showOffline)
            const InfoBanner(
                '🔒 Complete your profile (class, turnover, experience) to see which tenders you are eligible for.'),
          if (_showOffline)
            const InfoBanner(
                '🗞 Government tenders advertised in CG/UP newspapers. Tap to view the official notice, or add one you spotted.'),
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

  Widget _corrigendumsTile() {
    return Card(
      color: Brand.amber.withValues(alpha: 0.06),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 14),
          iconColor: Brand.amber,
          collapsedIconColor: Brand.amber,
          title: Text('⚠ ${_corrigendums.length} recent tender amendments',
              style: const TextStyle(
                  color: Brand.amber, fontSize: 13.5, fontWeight: FontWeight.w700)),
          subtitle: const Text('Dates/specs changed — verify before you bid',
              style: TextStyle(color: Brand.muted, fontSize: 11)),
          children: _corrigendums.take(25).map((c) {
            return ListTile(
              dense: true,
              title: Text(c.title,
                  style: const TextStyle(color: Brand.text, fontSize: 12.5)),
              subtitle: Text(
                  '📍 ${c.state}  ·  🔁 ${c.publishedDate}  ·  ⏰ new close ${c.closingDate}',
                  style: const TextStyle(color: Brand.muted, fontSize: 11)),
              trailing: (c.corrigendumUrl.isNotEmpty || c.tenderUrl.isNotEmpty)
                  ? IconButton(
                      icon: const Icon(Icons.open_in_new, size: 16, color: Brand.cyan),
                      onPressed: () => _open(c.corrigendumUrl.isNotEmpty
                          ? c.corrigendumUrl
                          : c.tenderUrl),
                    )
                  : null,
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _card(Tender t) {
    final verdict = Eligibility.verdict(t, _profile);
    final dl = t.daysLeft;
    final dlTxt = dl == null
        ? 'No deadline'
        : (dl < 0 ? '⚠ Expired' : '⏱ ${dl}d left');
    final id = '${t.raw['source_id'] ?? ''}';
    final saved = _saved.contains(id);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            InkWell(
              onTap: t.url.isNotEmpty ? () => _open(t.url) : null,
              child: Row(
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
            const Divider(height: 20, color: Brand.border),
            Row(children: [
              TextButton.icon(
                onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) =>
                            EvaluatorScreen(tender: t, profile: _profile))),
                icon: const Icon(Icons.insights, size: 16, color: Brand.cyan),
                label: const Text('Evaluate', style: TextStyle(color: Brand.cyan, fontSize: 12.5)),
                style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 8)),
              ),
              const Spacer(),
              IconButton(
                tooltip: saved ? 'Saved' : 'Save to pipeline',
                icon: Icon(saved ? Icons.bookmark : Icons.bookmark_border,
                    size: 20, color: saved ? Brand.green : Brand.muted),
                onPressed: () => _toggleSave(t),
              ),
            ]),
          ],
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

  // Manual capture of a newspaper tender → offline_tenders (public insert).
  Future<void> _captureOffline() async {
    final title = TextEditingController();
    final org = TextEditingController();
    final district = TextEditingController();
    final paper = TextEditingController();
    final url = TextEditingController();
    var state = 'Chhattisgarh';

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSt) => AlertDialog(
          backgroundColor: Brand.surface,
          title: const Text('Add newspaper tender', style: TextStyle(fontSize: 16)),
          content: SingleChildScrollView(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(controller: title, decoration: const InputDecoration(labelText: 'Title *')),
              const SizedBox(height: 8),
              TextField(controller: org, decoration: const InputDecoration(labelText: 'Department / org')),
              const SizedBox(height: 8),
              TextField(controller: district, decoration: const InputDecoration(labelText: 'District')),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                initialValue: state,
                dropdownColor: Brand.surface,
                decoration: const InputDecoration(labelText: 'State'),
                items: const ['Chhattisgarh', 'Uttar Pradesh']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => setSt(() => state = v ?? state),
              ),
              const SizedBox(height: 8),
              TextField(controller: paper, decoration: const InputDecoration(labelText: 'Newspaper')),
              const SizedBox(height: 8),
              TextField(controller: url, decoration: const InputDecoration(labelText: 'Link (optional)')),
            ]),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Save')),
          ],
        ),
      ),
    );
    if (ok != true || title.text.trim().isEmpty) return;

    final now = DateTime.now().millisecondsSinceEpoch;
    try {
      await Data.saveOfflineTenders([
        {
          'source_id': 'manual_${Data.email}_$now',
          'title': title.text.trim(),
          'organization': org.text.trim(),
          'district': district.text.trim(),
          'state': state,
          'newspaper': paper.text.trim(),
          'document_url': url.text.trim(),
        }
      ]);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('✓ Newspaper tender added')));
        _load();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Could not save: $e')));
      }
    }
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
