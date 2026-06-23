import 'package:flutter/material.dart';
import '../config.dart';

class SectionTitle extends StatelessWidget {
  final String text;
  const SectionTitle(this.text, {super.key});
  @override
  Widget build(BuildContext context) => Text(text,
      style: const TextStyle(
          color: Brand.text, fontSize: 20, fontWeight: FontWeight.w800));
}

class Chip2 extends StatelessWidget {
  final String label;
  final Color color;
  const Chip2(this.label, {super.key, this.color = Brand.muted});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.30)),
      ),
      child: Text(label,
          style: TextStyle(
              color: color == Brand.muted ? Brand.text : color,
              fontSize: 11,
              fontWeight: FontWeight.w600)),
    );
  }
}

class InfoBanner extends StatelessWidget {
  final String text;
  const InfoBanner(this.text, {super.key});
  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Brand.cyan.withOpacity(0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Brand.border),
      ),
      child: Text(text,
          style: const TextStyle(color: Brand.text, fontSize: 12.5, height: 1.4)),
    );
  }
}

class ErrorRetry extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const ErrorRetry({super.key, required this.message, required this.onRetry});
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.cloud_off, color: Brand.muted, size: 40),
          const SizedBox(height: 12),
          const Text('Could not load data',
              style: TextStyle(color: Brand.text, fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Text(message,
              textAlign: TextAlign.center,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Brand.muted, fontSize: 12)),
          const SizedBox(height: 16),
          FilledButton(onPressed: onRetry, child: const Text('Retry')),
        ]),
      ),
    );
  }
}
