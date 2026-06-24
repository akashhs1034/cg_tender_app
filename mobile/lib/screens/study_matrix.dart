import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../data.dart';
import '../intelligence.dart';
import '../portals.dart';
import 'widgets.dart';

/// Upcoming Exams & Study Matrix — generates a time-aware study plan for a
/// UP/CG government exam (AI via the Edge Function, rule-based fallback offline).
class StudyMatrixScreen extends StatefulWidget {
  const StudyMatrixScreen({super.key});
  @override
  State<StudyMatrixScreen> createState() => _StudyMatrixScreenState();
}

class _StudyMatrixScreenState extends State<StudyMatrixScreen> {
  final _examCtrl = TextEditingController();
  DateTime? _examDate;
  int _hours = 4;
  bool _busy = false;
  StudyPlan? _plan;

  Future<void> _generate() async {
    final exam = _examCtrl.text.trim();
    if (exam.isEmpty) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _busy = true;
      _plan = null;
    });
    final dateStr = _examDate?.toIso8601String().substring(0, 10) ?? '';
    final ai = await Data.studyPlan(exam: exam, examDate: dateStr, hours: _hours);
    StudyPlan plan;
    if (ai.isNotEmpty && ai['phases'] != null) {
      plan = StudyPlan.fromAi(ai);
    } else {
      final days = _examDate?.difference(DateTime.now()).inDays;
      plan = StudyPlan.fallback(exam, days, _hours);
    }
    if (mounted) {
      setState(() {
        _plan = plan;
        _busy = false;
      });
    }
  }

  Future<void> _open(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🧭 Exams & Study Matrix')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Pick an exam and get a focused, time-aware study plan.',
              style: TextStyle(color: Brand.muted, fontSize: 13)),
          const SizedBox(height: 14),
          TextField(
            controller: _examCtrl,
            decoration: const InputDecoration(
                labelText: 'Exam name',
                hintText: 'e.g. CGPSC State Service'),
          ),
          const SizedBox(height: 10),
          Wrap(spacing: 7, runSpacing: 2, children: [
            for (final e in commonExams)
              ActionChip(
                label: Text(e, style: const TextStyle(fontSize: 11.5)),
                backgroundColor: Brand.surface2,
                side: const BorderSide(color: Brand.border),
                onPressed: () => setState(() => _examCtrl.text = e),
              ),
          ]),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: DateTime.now().add(const Duration(days: 90)),
                    firstDate: DateTime.now(),
                    lastDate: DateTime(2100),
                  );
                  if (d != null) setState(() => _examDate = d);
                },
                icon: const Icon(Icons.event, size: 16, color: Brand.cyan),
                label: Text(
                    _examDate == null
                        ? 'Exam date (optional)'
                        : _examDate!.toIso8601String().substring(0, 10),
                    style: const TextStyle(color: Brand.cyan, fontSize: 12.5)),
                style: OutlinedButton.styleFrom(side: const BorderSide(color: Brand.border)),
              ),
            ),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            const Text('Hours/day', style: TextStyle(color: Brand.muted, fontSize: 13)),
            Expanded(
              child: Slider(
                value: _hours.toDouble(),
                min: 1,
                max: 12,
                divisions: 11,
                label: '$_hours h',
                activeColor: Brand.cyan,
                onChanged: (v) => setState(() => _hours = v.round()),
              ),
            ),
            Text('$_hours h', style: const TextStyle(color: Brand.text, fontSize: 13)),
          ]),
          const SizedBox(height: 6),
          FilledButton.icon(
            onPressed: _busy ? null : _generate,
            icon: const Icon(Icons.auto_awesome, size: 18),
            label: Text(_busy ? 'Building plan…' : 'Generate study plan'),
          ),
          if (_busy)
            const Padding(
                padding: EdgeInsets.only(top: 24),
                child: Center(child: CircularProgressIndicator())),
          if (_plan != null) ..._planWidgets(_plan!),

          const SizedBox(height: 24),
          const SectionTitle('📚 Free Study Resources'),
          const SizedBox(height: 8),
          for (final entry in studyResources.entries) ...[
            Text(entry.key,
                style: const TextStyle(
                    color: Brand.cyan, fontSize: 12.5, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            ...entry.value.map((p) => Card(
                  child: ListTile(
                    dense: true,
                    title: Text(p.label,
                        style: const TextStyle(color: Brand.text, fontSize: 13)),
                    trailing: const Icon(Icons.open_in_new, size: 15, color: Brand.cyan),
                    onTap: () => _open(p.url),
                  ),
                )),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }

  List<Widget> _planWidgets(StudyPlan p) {
    return [
      const SizedBox(height: 18),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('🧭 ${p.exam}',
                style: const TextStyle(
                    color: Brand.text, fontWeight: FontWeight.w800, fontSize: 15)),
            const SizedBox(height: 6),
            Text(p.overview,
                style: const TextStyle(color: Brand.muted, fontSize: 12.5, height: 1.5)),
            const SizedBox(height: 10),
            Wrap(spacing: 6, children: [
              if (p.daysLeft > 0) Chip2('⏳ ${p.daysLeft} days to exam'),
              Chip2(p.ai ? '⚡ Opporta Intelligence' : '📋 General template',
                  color: Brand.cyan),
            ]),
          ]),
        ),
      ),
      const SizedBox(height: 8),
      ...p.phases.map((ph) => Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(
                    child: Text(ph.name,
                        style: const TextStyle(
                            color: Brand.text, fontWeight: FontWeight.w700, fontSize: 13.5)),
                  ),
                  Text(ph.duration,
                      style: const TextStyle(color: Brand.green, fontSize: 11.5)),
                ]),
                const SizedBox(height: 4),
                Text(ph.focus, style: const TextStyle(color: Brand.muted, fontSize: 12)),
                const SizedBox(height: 8),
                Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: ph.topics.map((t) => Chip2(t)).toList()),
              ]),
            ),
          )),
      if (p.highPriority.isNotEmpty) ...[
        const SizedBox(height: 8),
        const Text('🔥 High-priority topics',
            style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        Wrap(
            spacing: 6,
            runSpacing: 6,
            children: p.highPriority.map((t) => Chip2(t, color: Brand.amber)).toList()),
      ],
      if (p.dailyRoutine.isNotEmpty) _bullets('🕒 Daily routine', p.dailyRoutine),
      if (p.freeResources.isNotEmpty) _bullets('📚 Resources to use', p.freeResources),
      if (p.tips.isNotEmpty) _bullets('💡 Tips', p.tips),
      const SizedBox(height: 12),
      Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Brand.amber.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Brand.amber.withValues(alpha: 0.25)),
        ),
        child: const Text(
          '⚠ Suggested plan — guidance only. This is an automated suggestion, not '
          'official and not a guarantee of syllabus coverage. Always confirm the '
          "official syllabus, pattern and dates on the authority's portal.",
          style: TextStyle(color: Brand.amber, fontSize: 11.5, height: 1.5),
        ),
      ),
    ];
  }

  Widget _bullets(String title, List<String> items) => Padding(
        padding: const EdgeInsets.only(top: 14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          ...items.map((x) => Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text('• $x',
                    style: const TextStyle(color: Brand.muted, fontSize: 12.5, height: 1.4)),
              )),
        ]),
      );
}
