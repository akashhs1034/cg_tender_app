import 'package:flutter/material.dart';
import '../config.dart';
import '../data.dart';

const _classes = ['Open', 'Class D', 'Class C', 'Class B', 'Class A', 'Unlimited'];
const _sectors = [
  'Civil & Construction', 'Water & Irrigation', 'Electrical & Energy',
  'Medical & Healthcare', 'IT & Technology', 'Transport & Logistics',
  'Manufacturing & Goods', 'Municipal Projects', 'Consultancy & Survey',
  'Police & Security', 'Government & Administration', 'Printing & Advertising',
];
const _statesOpts = ['Chhattisgarh', 'Uttar Pradesh'];

class ProfileEditScreen extends StatefulWidget {
  final Map<String, dynamic> initial;
  const ProfileEditScreen({super.key, required this.initial});
  @override
  State<ProfileEditScreen> createState() => _ProfileEditScreenState();
}

class _ProfileEditScreenState extends State<ProfileEditScreen> {
  late final TextEditingController _company;
  late final TextEditingController _turnover;
  late final TextEditingController _exp;
  late String _class;
  late Set<String> _selSectors;
  late Set<String> _selStates;
  bool _saving = false;
  String? _msg;

  @override
  void initState() {
    super.initState();
    final p = widget.initial;
    _company = TextEditingController(text: '${p['company_name'] ?? ''}');
    _turnover = TextEditingController(
        text: p['turnover_lakhs'] == null ? '' : '${p['turnover_lakhs']}');
    _exp = TextEditingController(
        text: p['experience_years'] == null ? '' : '${p['experience_years']}');
    _class = _classes.contains('${p['contractor_class']}')
        ? '${p['contractor_class']}'
        : 'Class C';
    _selSectors = _toSet(p['sectors']);
    _selStates = _toSet(p['states']);
    if (_selStates.isEmpty) _selStates = {'Chhattisgarh', 'Uttar Pradesh'};
  }

  Set<String> _toSet(dynamic v) =>
      v is List ? v.map((e) => '$e').toSet() : <String>{};

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _msg = null;
    });
    try {
      await Data.saveProfile({
        'company_name': _company.text.trim(),
        'contractor_class': _class,
        'turnover_lakhs': double.tryParse(_turnover.text.trim()) ?? 0,
        'experience_years': int.tryParse(_exp.text.trim()) ?? 0,
        'sectors': _selSectors.toList(),
        'states': _selStates.toList(),
      });
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _msg = 'Could not save: $e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Edit Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('These drive your Eligible / Not Eligible verdicts.',
              style: TextStyle(color: Brand.muted, fontSize: 12.5)),
          const SizedBox(height: 16),
          _label('Company name'),
          TextField(controller: _company),
          const SizedBox(height: 14),
          _label('Contractor class'),
          DropdownButtonFormField<String>(
            initialValue: _class,
            dropdownColor: Brand.surface,
            items: _classes
                .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                .toList(),
            onChanged: (v) => setState(() => _class = v ?? _class),
          ),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _label('Turnover (₹ lakhs)'),
              TextField(
                  controller: _turnover,
                  keyboardType: TextInputType.number),
            ])),
            const SizedBox(width: 12),
            Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _label('Experience (years)'),
              TextField(
                  controller: _exp, keyboardType: TextInputType.number),
            ])),
          ]),
          const SizedBox(height: 18),
          _label('States you operate in'),
          _chips(_statesOpts, _selStates),
          const SizedBox(height: 18),
          _label('Sectors'),
          _chips(_sectors, _selSectors),
          if (_msg != null) ...[
            const SizedBox(height: 14),
            Text(_msg!, style: const TextStyle(color: Brand.red, fontSize: 12.5)),
          ],
          const SizedBox(height: 22),
          FilledButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(
                    height: 20, width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Save profile'),
          ),
        ],
      ),
    );
  }

  Widget _label(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(t,
            style: const TextStyle(
                color: Brand.muted, fontSize: 12.5, fontWeight: FontWeight.w600)),
      );

  Widget _chips(List<String> opts, Set<String> sel) => Wrap(
        spacing: 8,
        runSpacing: 4,
        children: opts
            .map((o) => FilterChip(
                  label: Text(o, style: const TextStyle(fontSize: 12)),
                  selected: sel.contains(o),
                  selectedColor: Brand.cyan.withValues(alpha: 0.22),
                  checkmarkColor: Brand.cyan,
                  backgroundColor: Brand.surface2,
                  onSelected: (v) => setState(
                      () => v ? sel.add(o) : sel.remove(o)),
                ))
            .toList(),
      );
}
