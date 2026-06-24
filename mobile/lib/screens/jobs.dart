import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../data.dart';
import 'widgets.dart';
import 'resume_analyzer.dart';
import 'study_matrix.dart';
import 'portals_screen.dart';

class JobsScreen extends StatefulWidget {
  const JobsScreen({super.key});
  @override
  State<JobsScreen> createState() => _JobsScreenState();
}

class _JobsScreenState extends State<JobsScreen> {
  List<Job> _all = [];
  bool _loading = true;
  String? _error;
  String _q = '';
  String _state = 'All';

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
      _all = await Data.jobs();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<Job> get _filtered {
    final q = _q.toLowerCase();
    return _all.where((j) {
      if (q.isNotEmpty &&
          !('${j.title} ${j.dept} ${j.qualification}'.toLowerCase().contains(q))) {
        return false;
      }
      if (_state != 'All' && j.state != _state) return false;
      return true;
    }).toList();
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
    if (_error != null) return ErrorRetry(message: _error!, onRetry: _load);
    final rows = _filtered;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
        children: [
          Row(children: [
            const Expanded(child: SectionTitle('💼 Government Jobs')),
            IconButton(
              tooltip: 'Recruitment portals',
              icon: const Icon(Icons.public, color: Brand.cyan),
              onPressed: () => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const PortalsScreen())),
            ),
          ]),
          const SizedBox(height: 6),
          FilledButton.icon(
            onPressed: () => Navigator.push(context,
                MaterialPageRoute(builder: (_) => const StudyMatrixScreen())),
            icon: const Icon(Icons.auto_stories, size: 18),
            label: const Text('🧭  Exams & Study Matrix'),
            style: FilledButton.styleFrom(
                backgroundColor: Brand.blue, foregroundColor: Colors.white),
          ),
          const SizedBox(height: 12),
          TextField(
            decoration: const InputDecoration(
                hintText: 'Search title, department, qualification…',
                prefixIcon: Icon(Icons.search, color: Brand.muted)),
            onChanged: (v) => setState(() => _q = v),
          ),
          const SizedBox(height: 10),
          Wrap(spacing: 8, children: [
            for (final s in ['All', 'Chhattisgarh', 'Uttar Pradesh'])
              ChoiceChip(
                label: Text(s),
                selected: _state == s,
                onSelected: (_) => setState(() => _state = s),
                selectedColor: Brand.cyan.withValues(alpha: 0.2),
              ),
          ]),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Text('${rows.length} postings',
                style: const TextStyle(color: Brand.muted, fontSize: 12)),
          ),
          ...rows.take(120).map((j) => Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      InkWell(
                        onTap: j.url.isNotEmpty ? () => _open(j.url) : null,
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: Text(j.title,
                                  style: const TextStyle(
                                      color: Brand.text,
                                      fontWeight: FontWeight.w700,
                                      height: 1.3)),
                            ),
                            if (j.url.isNotEmpty)
                              const Icon(Icons.open_in_new,
                                  size: 16, color: Brand.cyan),
                          ],
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text('🏛 ${j.dept}  ·  ${j.state}',
                          style: const TextStyle(color: Brand.muted, fontSize: 12)),
                      const SizedBox(height: 10),
                      Wrap(spacing: 6, runSpacing: 6, children: [
                        if (j.vacancies.isNotEmpty)
                          Chip2('👥 ${j.vacancies} posts'),
                        if (j.qualification.isNotEmpty)
                          Chip2('🎓 ${j.qualification}'),
                        if (j.deadline.isNotEmpty) Chip2('⏱ ${j.deadline}'),
                      ]),
                      const Divider(height: 20, color: Brand.border),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton.icon(
                          onPressed: () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                  builder: (_) => ResumeAnalyzerScreen(job: j))),
                          icon: const Icon(Icons.fact_check_outlined,
                              size: 16, color: Brand.cyan),
                          label: const Text('Resume match',
                              style: TextStyle(color: Brand.cyan, fontSize: 12.5)),
                          style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(horizontal: 8)),
                        ),
                      ),
                    ],
                  ),
                ),
              )),
        ],
      ),
    );
  }
}
