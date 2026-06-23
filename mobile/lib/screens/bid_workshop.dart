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

  List<Widget> _resultWidgets() {
    final t = Map<String, dynamic>.from(_result!['tender'] ?? {});
    final tender = Tender(t);
    final verdict = Eligibility.verdict(tender, _profile);
    final compliance =
        (_result!['compliance'] as List?)?.cast<dynamic>() ?? const [];
    final manual =
        (_result!['manual_actions'] as List?)?.cast<dynamic>() ?? const [];

    Color vColor = verdict == 'ELIGIBLE'
        ? Brand.green
        : (verdict == 'NOT ELIGIBLE' ? Brand.red : Brand.muted);
    String vText = verdict == 'ELIGIBLE'
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
      const SizedBox(height: 18),
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
      if (compliance.isNotEmpty) ...[
        const SizedBox(height: 18),
        const Text('📊 Compliance',
            style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
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
      if (manual.isNotEmpty) ...[
        const SizedBox(height: 18),
        const Text('✍️ Manual actions (do these yourself)',
            style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
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
      const SizedBox(height: 24),
    ];
  }
}
