import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../data.dart';
import '../intelligence.dart';
import 'widgets.dart';

/// Tender Evaluator — the web app's 6-dimension opportunity scoring with
/// reasoning, on top of the binary eligibility gate. Pure on-device (rule-based).
class EvaluatorScreen extends StatelessWidget {
  final Tender tender;
  final Map<String, dynamic> profile;
  const EvaluatorScreen({super.key, required this.tender, required this.profile});

  Color _scoreColor(int s) =>
      s >= 75 ? Brand.green : (s >= 50 ? Brand.amber : Brand.red);

  Future<void> _open() async {
    final uri = Uri.tryParse(tender.url);
    if (uri != null && tender.url.startsWith('http')) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final configured = Eligibility.profileConfigured(profile);
    final verdict = Eligibility.verdict(tender, profile);
    final score = Scorer.score(tender, profile);
    final overall = score.overall;

    return Scaffold(
      appBar: AppBar(title: const Text('🔍 Tender Evaluator')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(tender.title,
              style: const TextStyle(
                  color: Brand.text, fontWeight: FontWeight.w800, fontSize: 16, height: 1.3)),
          const SizedBox(height: 4),
          Text('🏛 ${tender.org}  ·  ${tender.state}',
              style: const TextStyle(color: Brand.muted, fontSize: 12)),
          const SizedBox(height: 14),
          if (!configured)
            const InfoBanner(
                '🔒 Complete your contractor profile (class, turnover, experience) for an accurate score.'),

          // ── Overall score ring ──────────────────────────────────────────────
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Row(children: [
                _ring(overall),
                const SizedBox(width: 18),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('Opportunity score',
                        style: TextStyle(color: Brand.muted, fontSize: 12)),
                    const SizedBox(height: 4),
                    Text(score.verdict,
                        style: const TextStyle(
                            color: Brand.text, fontWeight: FontWeight.w700, height: 1.3)),
                    const SizedBox(height: 8),
                    Wrap(spacing: 6, runSpacing: 6, children: [
                      if (verdict == 'ELIGIBLE')
                        const Chip2('✅ Eligible', color: Brand.green),
                      if (verdict == 'NOT ELIGIBLE')
                        const Chip2('❌ Not Eligible', color: Brand.red),
                      Chip2('💰 ${tender.valueLabel}'),
                    ]),
                  ]),
                ),
              ]),
            ),
          ),
          const SizedBox(height: 8),
          const Text('Score breakdown',
              style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          ...score.dimensions.map(_dimension),

          const SizedBox(height: 16),
          if (tender.url.isNotEmpty)
            OutlinedButton.icon(
              onPressed: _open,
              icon: const Icon(Icons.open_in_new, size: 18, color: Brand.cyan),
              label: const Text('Open official tender', style: TextStyle(color: Brand.cyan)),
              style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(46),
                  side: const BorderSide(color: Brand.border)),
            ),
          const SizedBox(height: 12),
          const Text(
            'Scores are an automated estimate from the tender facts + your profile — '
            'guidance only. Verify the official document before bidding.',
            style: TextStyle(color: Brand.muted, fontSize: 11, height: 1.5),
          ),
        ],
      ),
    );
  }

  Widget _ring(int score) {
    final c = _scoreColor(score);
    return SizedBox(
      width: 78,
      height: 78,
      child: Stack(alignment: Alignment.center, children: [
        SizedBox(
          width: 78,
          height: 78,
          child: CircularProgressIndicator(
            value: score / 100,
            strokeWidth: 7,
            backgroundColor: Brand.surface2,
            valueColor: AlwaysStoppedAnimation(c),
          ),
        ),
        Text('$score',
            style: TextStyle(color: c, fontSize: 22, fontWeight: FontWeight.w900)),
      ]),
    );
  }

  Widget _dimension(ScoreDimension d) {
    final isRisk = d.key == 'competition';
    final shown = isRisk ? 100 - d.score : d.score;
    final c = _scoreColor(shown);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(d.label,
              style: const TextStyle(color: Brand.text, fontSize: 13, fontWeight: FontWeight.w600)),
          Text(isRisk ? '${d.score}% risk' : '${d.score}',
              style: TextStyle(color: c, fontSize: 12, fontWeight: FontWeight.w700)),
        ]),
        const SizedBox(height: 5),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(
            value: shown / 100,
            minHeight: 7,
            backgroundColor: Brand.surface2,
            valueColor: AlwaysStoppedAnimation(c),
          ),
        ),
        const SizedBox(height: 5),
        ...d.reasons.map((r) => Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text('• $r',
                  style: const TextStyle(color: Brand.muted, fontSize: 11.5, height: 1.4)),
            )),
      ]),
    );
  }
}
