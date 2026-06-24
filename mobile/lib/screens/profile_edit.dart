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
const _degreeOptions = [
  'B.Tech / B.E. (Engineering)', 'MBA / PGDM', 'MCA', 'M.Tech / M.E.',
  'B.Ed (Teacher Training)', 'MBBS / Medical Degree', 'GNM / B.Sc Nursing',
  '12th / Intermediate', 'Diploma', 'B.Sc / B.A. / B.Com (Graduate)',
  'Ph.D / Post-Graduate (Other)',
];
const _categoryOptions = ['General', 'OBC', 'SC', 'ST', 'EWS'];
const _langOptions = ['Hindi', 'English', 'Chhattisgarhi', 'Awadhi', 'Bhojpuri', 'Urdu'];

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
  // Job-seeker fields
  late final TextEditingController _fullName;
  late final TextEditingController _jobExp;
  late final TextEditingController _skills;
  late final TextEditingController _qualification;
  late String _degree;
  late String _jobCategory;
  late Set<String> _languages;
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

    _fullName = TextEditingController(text: '${p['full_name'] ?? ''}');
    _jobExp = TextEditingController(
        text: p['job_experience_years'] == null ? '' : '${p['job_experience_years']}');
    _skills = TextEditingController(
        text: (p['job_skills'] is List) ? (p['job_skills'] as List).join(', ') : '');
    _qualification = TextEditingController(text: '${p['qualification'] ?? ''}');
    _degree =
        _degreeOptions.contains('${p['degree_type']}') ? '${p['degree_type']}' : _degreeOptions.first;
    _jobCategory =
        _categoryOptions.contains('${p['job_category']}') ? '${p['job_category']}' : 'General';
    _languages = _toSet(p['languages']);
    if (_languages.isEmpty) _languages = {'Hindi', 'English'};
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
        // Job-seeker profile (drives Resume Analyzer + job matching)
        'full_name': _fullName.text.trim(),
        'degree_type': _degree,
        'job_category': _jobCategory,
        'job_experience_years': int.tryParse(_jobExp.text.trim()) ?? 0,
        'languages': _languages.toList(),
        'job_skills': _skills.text
            .split(',')
            .map((s) => s.trim())
            .where((s) => s.isNotEmpty)
            .toList(),
        'qualification': _qualification.text.trim(),
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

          const SizedBox(height: 26),
          const Divider(color: Brand.border),
          const SizedBox(height: 8),
          const Text('💼 Job Seeker Profile',
              style: TextStyle(
                  color: Brand.text, fontSize: 15, fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          const Text('Powers the Resume Analyzer & job-match — optional.',
              style: TextStyle(color: Brand.muted, fontSize: 12)),
          const SizedBox(height: 16),
          _label('Full name'),
          TextField(controller: _fullName),
          const SizedBox(height: 14),
          _label('Highest degree / qualification'),
          DropdownButtonFormField<String>(
            initialValue: _degree,
            dropdownColor: Brand.surface,
            isExpanded: true,
            items: _degreeOptions
                .map((c) => DropdownMenuItem(
                    value: c, child: Text(c, overflow: TextOverflow.ellipsis)))
                .toList(),
            onChanged: (v) => setState(() => _degree = v ?? _degree),
          ),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _label('Reservation category'),
              DropdownButtonFormField<String>(
                initialValue: _jobCategory,
                dropdownColor: Brand.surface,
                items: _categoryOptions
                    .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                    .toList(),
                onChanged: (v) => setState(() => _jobCategory = v ?? _jobCategory),
              ),
            ])),
            const SizedBox(width: 12),
            Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _label('Work experience (yrs)'),
              TextField(controller: _jobExp, keyboardType: TextInputType.number),
            ])),
          ]),
          const SizedBox(height: 14),
          _label('Languages known'),
          _chips(_langOptions, _languages),
          const SizedBox(height: 14),
          _label('Key skills (comma-separated)'),
          TextField(
              controller: _skills,
              decoration: const InputDecoration(
                  hintText: 'e.g. AutoCAD, MS Office, Tally, Python')),
          const SizedBox(height: 14),
          _label('Qualification details'),
          TextField(
              controller: _qualification,
              maxLines: 3,
              decoration: const InputDecoration(
                  hintText: 'e.g. B.Tech Civil, NIT Raipur, 2018, 75%')),
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
