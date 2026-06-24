import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../portals.dart';
import 'widgets.dart';

/// Official government portal directory — verified procurement + recruitment
/// portals so users can always reach the authoritative source directly.
class PortalsScreen extends StatelessWidget {
  const PortalsScreen({super.key});

  Future<void> _open(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🌐 Official Portals')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
        children: [
          const InfoBanner(
              'Verified government portals — open the authoritative source directly. Opporta aggregates from these, but always confirm on the official site before bidding/applying.'),
          const SizedBox(height: 14),
          _group('🏛 Tender / Procurement Portals', procurementPortals),
          const SizedBox(height: 14),
          _group('🎓 Recruitment Authorities', recruitmentAuthorities),
          const SizedBox(height: 14),
          _group('📚 Free Study Resources', studyResources),
        ],
      ),
    );
  }

  Widget _group(String title, Map<String, List<Portal>> data) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SectionTitle(title),
      const SizedBox(height: 8),
      for (final entry in data.entries) ...[
        Padding(
          padding: const EdgeInsets.only(top: 4, bottom: 6),
          child: Text(entry.key,
              style: const TextStyle(
                  color: Brand.cyan, fontSize: 12.5, fontWeight: FontWeight.w700)),
        ),
        ...entry.value.map((p) => Card(
              child: ListTile(
                dense: true,
                title: Text(p.label,
                    style: const TextStyle(color: Brand.text, fontSize: 13)),
                subtitle: Text(p.url,
                    style: const TextStyle(color: Brand.muted, fontSize: 11)),
                trailing: const Icon(Icons.open_in_new, size: 16, color: Brand.cyan),
                onTap: () => _open(p.url),
              ),
            )),
        const SizedBox(height: 6),
      ],
    ]);
  }
}
