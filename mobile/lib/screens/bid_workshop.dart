import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:file_picker/file_picker.dart';
import '../config.dart';
import '../data.dart';

class BidWorkshopScreen extends StatefulWidget {
  const BidWorkshopScreen({super.key});
  @override
  State<BidWorkshopScreen> createState() => _BidWorkshopScreenState();
}

class _BidWorkshopScreenState extends State<BidWorkshopScreen> {
  bool _busy = false;
  String? _error;
  String? _fileName;
  Map<String, dynamic>? _result;
  Map<String, dynamic> _profile = {};
  final _coverCtrl = TextEditingController();
  final _done = <int>{};

  String _mime(String fn) {
    final e = fn.toLowerCase();
    if (e.endsWith('.png')) return 'image/png';
    if (e.endsWith('.jpg') || e.endsWith('.jpeg')) return 'image/jpeg';
    return 'application/pdf';
  }

  Future<void> _pickAndDraft() async {
    final res = await FilePicker.platform.pickFiles(
      withData: true,
      type: FileType.custom,
      allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
    );
    if (res == null || res.files.isEmpty || res.files.first.bytes == null) return;
    final f = res.files.first;
    setState(() {
      _busy = true;
      _error = null;
      _result = null;
      _fileName = f.name;
      _done.clear();
    });
    try {
      _profile = await Data.profile();
      final out = await Data.draftBid(
        docBase64: base64Encode(f.bytes!),
        mimeType: _mime(f.name),
        profile: _profile,
      );
      if (out['error'] != null) {
        _error = 'Could not draft the bid (${out['error']}). '
            'Make sure the bid-engine function is deployed with GEMINI_API_KEY set.';
      } else {
        _result = out;
        _coverCtrl.text = '${out['cover_letter'] ?? ''}';
      }
    } catch (e) {
      _error = '$e';
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🛠 Bid Workshop')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
              'Upload the tender / NIT document. Opporta Intelligence reads it, '
              'checks your eligibility, and drafts a ready-to-submit bid.',
              style: TextStyle(color: Brand.muted, fontSize: 13)),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _busy ? null : _pickAndDraft,
            icon: const Icon(Icons.upload_file),
            label: Text(_busy ? 'Drafting…' : 'Upload tender & draft bid'),
          ),
          if (_fileName != null && !_busy)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text('📄 $_fileName',
                  style: const TextStyle(color: Brand.muted, fontSize: 12)),
            ),
          if (_busy)
            const Padding(
                padding: EdgeInsets.only(top: 24),
                child: Center(child: CircularProgressIndicator())),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Text(_error!,
                  style: const TextStyle(color: Brand.red, fontSize: 12.5)),
            ),
          if (_result != null) ..._resultWidgets(),
        ],
      ),
    );
  }

  String _s(dynamic v) => (v == null) ? '' : '$v'.trim();
  List<String> _l(dynamic v) =>
      (v is List) ? v.map((e) => '$e').toList() : const <String>[];

  /// Assemble the whole bid (every section) as plain text to paste into Word/email.
  String _fullBidText() {
    final r = _result!;
    final t = Map<String, dynamic>.from(r['tender'] ?? {});
    final cp = Map<String, dynamic>.from(r['company_profile'] ?? {});
    final tp = Map<String, dynamic>.from(r['technical_proposal'] ?? {});
    final b = StringBuffer()
      ..writeln(_s(t['title']).isEmpty ? 'Tender Bid' : _s(t['title']))
      ..writeln(_s(t['organization']))
      ..writeln('\n== COVER LETTER ==\n${_coverCtrl.text}');
    if (_s(cp['overview']).isNotEmpty || _l(cp['key_strengths']).isNotEmpty) {
      b.writeln('\n== COMPANY PROFILE ==\n${_s(cp['overview'])}');
      for (final s in _l(cp['key_strengths'])) {
        b.writeln('• $s');
      }
    }
    if (tp.isNotEmpty) {
      b.writeln('\n== TECHNICAL PROPOSAL ==\n${_s(tp['scope_understanding'])}');
      for (final m in _l(tp['methodology'])) {
        b.writeln('• $m');
      }
      if (_s(tp['team_structure']).isNotEmpty) b.writeln('Team: ${_s(tp['team_structure'])}');
      if (_s(tp['quality_assurance']).isNotEmpty) b.writeln('QA: ${_s(tp['quality_assurance'])}');
      if (_s(tp['timeline_overview']).isNotEmpty) b.writeln('Timeline: ${_s(tp['timeline_overview'])}');
    }
    for (final c in (r['compliance'] as List? ?? const [])) {
      final m = Map<String, dynamic>.from(c as Map);
      b.writeln('Compliance: ${m['requirement']} — ${m['our_response']} (${m['status']})');
    }
    for (final c in (r['document_checklist'] as List? ?? const [])) {
      final m = Map<String, dynamic>.from(c as Map);
      b.writeln('Doc: ${m['document']} — ${m['status']}');
    }
    for (final m in _l(r['manual_actions'])) {
      b.writeln('Arrange yourself: $m');
    }
    if (_s(r['declaration']).isNotEmpty) b.writeln('\n== DECLARATION ==\n${_s(r['declaration'])}');
    return b.toString();
  }

  void _copyFullBid() {
    Clipboard.setData(ClipboardData(text: _fullBidText()));
    ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Full bid copied — paste into Word or email')));
  }

  Widget _secTitle(String t) => Padding(
        padding: const EdgeInsets.only(top: 18, bottom: 6),
        child: Text(t,
            style: const TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
      );
  Widget _para(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(t,
            style: const TextStyle(color: Brand.text, fontSize: 12.5, height: 1.5)),
      );
  Widget _bullet(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 3),
        child: Text('• $t',
            style: const TextStyle(color: Brand.muted, fontSize: 12.5, height: 1.4)),
      );

  List<Widget> _resultWidgets() {
    final r = _result!;
    final tender = Tender(Map<String, dynamic>.from(r['tender'] ?? {}));
    final verdict = Eligibility.verdict(tender, _profile);
    final cp = Map<String, dynamic>.from(r['company_profile'] ?? {});
    final tp = Map<String, dynamic>.from(r['technical_proposal'] ?? {});
    final compliance = (r['compliance'] as List?) ?? const [];
    final checklist = (r['document_checklist'] as List?) ?? const [];
    final manual = (r['manual_actions'] as List?) ?? const [];
    final declaration = _s(r['declaration']);

    final vColor = verdict == 'ELIGIBLE'
        ? Brand.green
        : (verdict == 'NOT ELIGIBLE' ? Brand.red : Brand.muted);
    final vText = verdict == 'ELIGIBLE'
        ? '✅ Eligible'
        : (verdict == 'NOT ELIGIBLE'
            ? '❌ Not Eligible'
            : '🔒 Complete profile to check eligibility');

    return [
      const SizedBox(height: 18),
      Text(tender.title,
          style: const TextStyle(
              color: Brand.text, fontWeight: FontWeight.w800, fontSize: 15)),
      const SizedBox(height: 4),
      Text('🏛 ${tender.org}',
          style: const TextStyle(color: Brand.muted, fontSize: 12)),
      const SizedBox(height: 12),
      Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: vColor.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: vColor.withValues(alpha: 0.30)),
        ),
        child: Text(vText,
            style: TextStyle(color: vColor, fontWeight: FontWeight.w700)),
      ),
      const SizedBox(height: 12),
      FilledButton.icon(
        onPressed: _copyFullBid,
        icon: const Icon(Icons.copy_all, size: 18),
        label: const Text('Copy full bid (all sections)'),
        style: FilledButton.styleFrom(
            backgroundColor: Brand.green, foregroundColor: const Color(0xFF02040A)),
      ),
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        const Text('📝 Cover letter (editable)',
            style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
        TextButton.icon(
          onPressed: () {
            Clipboard.setData(ClipboardData(text: _coverCtrl.text));
            ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Cover letter copied')));
          },
          icon: const Icon(Icons.copy, size: 16),
          label: const Text('Copy'),
        ),
      ]),
      const SizedBox(height: 6),
      TextField(controller: _coverCtrl, maxLines: 12),
      if (_s(cp['overview']).isNotEmpty || _l(cp['key_strengths']).isNotEmpty) ...[
        _secTitle('🏢 Company profile'),
        if (_s(cp['overview']).isNotEmpty) _para(_s(cp['overview'])),
        ..._l(cp['key_strengths']).map(_bullet),
      ],
      if (tp.isNotEmpty) ...[
        _secTitle('🔧 Technical proposal'),
        if (_s(tp['scope_understanding']).isNotEmpty) _para(_s(tp['scope_understanding'])),
        ..._l(tp['methodology']).map(_bullet),
        if (_s(tp['team_structure']).isNotEmpty) _para('👷 Team: ${_s(tp['team_structure'])}'),
        if (_s(tp['quality_assurance']).isNotEmpty) _para('✓ QA: ${_s(tp['quality_assurance'])}'),
        if (_s(tp['timeline_overview']).isNotEmpty) _para('🗓 Timeline: ${_s(tp['timeline_overview'])}'),
      ],
      if (compliance.isNotEmpty) ...[
        _secTitle('📊 Compliance'),
        ...compliance.map((c) {
          final m = Map<String, dynamic>.from(c as Map);
          return Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${m['requirement'] ?? ''}',
                    style: const TextStyle(
                        color: Brand.text, fontWeight: FontWeight.w600, fontSize: 13)),
                const SizedBox(height: 2),
                Text('${m['our_response'] ?? ''}  ·  ${m['status'] ?? ''}',
                    style: const TextStyle(color: Brand.muted, fontSize: 12)),
              ]),
            ),
          );
        }),
      ],
      if (checklist.isNotEmpty) ...[
        _secTitle('📎 Document checklist'),
        ...checklist.map((c) {
          final m = Map<String, dynamic>.from(c as Map);
          return _bullet('${m['document'] ?? ''} — ${m['status'] ?? ''}');
        }),
      ],
      if (manual.isNotEmpty) ...[
        _secTitle('✍️ Arrange yourself (do these)'),
        ...List.generate(manual.length, (i) {
          return CheckboxListTile(
            value: _done.contains(i),
            onChanged: (v) => setState(
                () => v == true ? _done.add(i) : _done.remove(i)),
            controlAffinity: ListTileControlAffinity.leading,
            contentPadding: EdgeInsets.zero,
            dense: true,
            title: Text('${manual[i]}',
                style: const TextStyle(color: Brand.text, fontSize: 12.5)),
          );
        }),
      ],
      if (declaration.isNotEmpty) ...[
        _secTitle('📜 Declaration'),
        _para(declaration),
      ],
      const SizedBox(height: 24),
    ];
  }
}
