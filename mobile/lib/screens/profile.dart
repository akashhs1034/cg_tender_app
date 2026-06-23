import 'package:flutter/material.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';

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

  String _f(String key, [String d = 'Not set']) {
    final v = _profile[key];
    return (v == null || '$v'.trim().isEmpty) ? d : '$v';
  }

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
                'ℹ️ Add your contractor class, turnover & experience (on the web app for now) so Opporta can tell you which tenders you are eligible for.'),
          const SizedBox(height: 6),
          _row('Company', _f('company_name')),
          _row('Contractor class', _f('contractor_class')),
          _row('Turnover (₹ lakhs)', _f('turnover_lakhs')),
          _row('Experience (years)', _f('experience_years')),
          _row('Sectors', _f('sectors')),
          _row('States', _f('states')),
          const SizedBox(height: 16),
          const SectionTitle('📄 Document Vault'),
          const SizedBox(height: 8),
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
