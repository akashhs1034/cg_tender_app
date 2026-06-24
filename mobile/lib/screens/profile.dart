import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';
import 'profile_edit.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic> _profile = {};
  List<Map<String, dynamic>> _docs = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final results = await Future.wait([Data.profile(), Data.documents()]);
    _profile = results[0] as Map<String, dynamic>;
    _docs = results[1] as List<Map<String, dynamic>>;
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _editProfile() async {
    final changed = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => ProfileEditScreen(initial: _profile)),
    );
    if (changed == true) _load();
  }

  String _mime(String fn) {
    final e = fn.toLowerCase();
    if (e.endsWith('.pdf')) return 'application/pdf';
    if (e.endsWith('.png')) return 'image/png';
    if (e.endsWith('.jpg') || e.endsWith('.jpeg')) return 'image/jpeg';
    if (e.endsWith('.txt')) return 'text/plain';
    return 'application/octet-stream';
  }

  Future<void> _uploadDoc() async {
    final res = await FilePicker.platform.pickFiles(
      withData: true,
      type: FileType.custom,
      allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png', 'txt', 'docx'],
    );
    if (res == null || res.files.isEmpty || res.files.first.bytes == null) return;
    final f = res.files.first;
    if (!mounted) return;

    final labelCtrl = TextEditingController(text: f.name);
    DateTime? expiry;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSt) => AlertDialog(
          backgroundColor: Brand.surface,
          title: const Text('Add to vault', style: TextStyle(fontSize: 16)),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(
                controller: labelCtrl,
                decoration: const InputDecoration(labelText: 'Document label')),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(
                  child: Text(
                      expiry == null
                          ? 'No expiry set'
                          : 'Valid until ${expiry!.toIso8601String().substring(0, 10)}',
                      style: const TextStyle(color: Brand.muted, fontSize: 12))),
              TextButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: ctx,
                    initialDate: DateTime.now().add(const Duration(days: 365)),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2100),
                  );
                  if (d != null) setSt(() => expiry = d);
                },
                child: const Text('Set expiry'),
              ),
            ]),
          ]),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Cancel')),
            FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('Upload')),
          ],
        ),
      ),
    );
    if (ok != true) return;

    try {
      await Data.uploadDocument(
        name: labelCtrl.text.trim().isEmpty ? f.name : labelCtrl.text.trim(),
        filename: f.name,
        bytes: Uint8List.fromList(f.bytes!),
        mimeType: _mime(f.name),
        expiryDate: expiry?.toIso8601String().substring(0, 10),
        docType: 'Other',
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('✓ Uploaded to vault')));
        _load();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Upload failed: $e')));
      }
    }
  }

  Future<void> _openDoc(Map<String, dynamic> d) async {
    final url = await Data.documentUrl(d);
    if (url == null) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Could not open document')));
      }
      return;
    }
    final uri = Uri.tryParse(url);
    if (uri != null) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Future<void> _deleteDoc(Map<String, dynamic> d) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: Brand.surface,
        title: const Text('Delete document?', style: TextStyle(fontSize: 16)),
        content: Text('${d['name'] ?? d['filename'] ?? 'This document'} will be removed from your vault.',
            style: const TextStyle(color: Brand.muted, fontSize: 13)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(
              style: FilledButton.styleFrom(backgroundColor: Brand.red),
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Delete')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await Data.deleteDocument(d);
      if (mounted) _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Delete failed: $e')));
      }
    }
  }

  String _f(String key, [String d = 'Not set']) {
    final v = _profile[key];
    if (v is List) return v.isEmpty ? d : v.join(', ');
    return (v == null || '$v'.trim().isEmpty) ? d : '$v';
  }

  bool get _hasJobProfile =>
      _f('full_name', '').isNotEmpty ||
      _f('qualification', '').isNotEmpty ||
      _f('job_skills', '').isNotEmpty;

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    final configured = Eligibility.profileConfigured(_profile);
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
        children: [
          const SectionTitle('👤 Profile'),
          const SizedBox(height: 10),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(Data.email,
                    style: const TextStyle(
                        color: Brand.text, fontWeight: FontWeight.w700, fontSize: 15)),
                const SizedBox(height: 4),
                Text(configured ? '✅ Profile configured' : '⚠ Profile incomplete',
                    style: TextStyle(
                        color: configured ? Brand.green : Brand.amber, fontSize: 12)),
              ]),
            ),
          ),
          if (!configured)
            const InfoBanner(
                'ℹ️ Add your contractor class, turnover & experience so Opporta can tell you which tenders you are eligible for.'),
          const SizedBox(height: 10),
          FilledButton.icon(
            onPressed: _editProfile,
            icon: const Icon(Icons.edit, size: 18),
            label: const Text('Edit profile'),
          ),
          const SizedBox(height: 6),
          _row('Company', _f('company_name')),
          _row('Contractor class', _f('contractor_class')),
          _row('Turnover (₹ lakhs)', _f('turnover_lakhs')),
          _row('Experience (years)', _f('experience_years')),
          _row('Sectors', _f('sectors')),
          _row('States', _f('states')),
          if (_hasJobProfile) ...[
            const SizedBox(height: 16),
            const SectionTitle('💼 Job Seeker Profile'),
            const SizedBox(height: 6),
            _row('Full name', _f('full_name')),
            _row('Degree', _f('degree_type')),
            _row('Category', _f('job_category')),
            _row('Experience (yrs)', _f('job_experience_years')),
            _row('Languages', _f('languages')),
            _row('Skills', _f('job_skills')),
            _row('Qualification', _f('qualification')),
          ],
          const SizedBox(height: 16),
          const SectionTitle('📄 Document Vault'),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _uploadDoc,
            icon: const Icon(Icons.upload_file, size: 18, color: Brand.cyan),
            label: const Text('Upload document',
                style: TextStyle(color: Brand.cyan)),
            style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(46),
                side: const BorderSide(color: Brand.border)),
          ),
          const SizedBox(height: 10),
          Text('${_docs.length} document(s)',
              style: const TextStyle(color: Brand.muted, fontSize: 12)),
          const SizedBox(height: 6),
          ..._docs.map((d) => Card(
                child: ListTile(
                  leading: const Icon(Icons.insert_drive_file, color: Brand.cyan),
                  title: Text('${d['name'] ?? d['filename'] ?? 'Document'}',
                      style: const TextStyle(color: Brand.text, fontSize: 13)),
                  subtitle: Text(_docSubtitle(d),
                      style: const TextStyle(color: Brand.muted, fontSize: 11)),
                  trailing: PopupMenuButton<String>(
                    icon: const Icon(Icons.more_vert, color: Brand.muted),
                    color: Brand.surface,
                    onSelected: (v) =>
                        v == 'open' ? _openDoc(d) : _deleteDoc(d),
                    itemBuilder: (_) => const [
                      PopupMenuItem(value: 'open', child: Text('Open / Download')),
                      PopupMenuItem(value: 'delete', child: Text('Delete')),
                    ],
                  ),
                ),
              )),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () async => Data.signOut(),
            icon: const Icon(Icons.logout, color: Brand.red),
            label: const Text('Log out', style: TextStyle(color: Brand.red)),
            style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(48),
                side: const BorderSide(color: Brand.red)),
          ),
        ],
      ),
    );
  }

  String _docSubtitle(Map<String, dynamic> d) {
    final exp = '${d['expiry_date'] ?? ''}'.trim();
    if (exp.isEmpty) return '${d['filename'] ?? ''}';
    final ed = DateTime.tryParse(exp);
    if (ed == null) return 'Valid until $exp';
    final days = ed.difference(DateTime.now()).inDays;
    if (days < 0) return '⛔ Expired $exp';
    if (days <= 30) return '⚠ Expires in ${days}d ($exp)';
    return '✅ Valid until $exp';
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 7),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(
              width: 140,
              child: Text(label,
                  style: const TextStyle(color: Brand.muted, fontSize: 12.5))),
          Expanded(
              child: Text(value,
                  style: const TextStyle(color: Brand.text, fontSize: 12.5))),
        ]),
      );
}
