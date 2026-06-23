import 'package:flutter/material.dart';
import '../config.dart';
import '../data.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _pass = TextEditingController();
  bool _busy = false;
  bool _register = false;
  String? _msg;

  Future<void> _submit() async {
    if (_email.text.trim().isEmpty || _pass.text.length < 6) {
      setState(() => _msg = 'Enter your email and a 6+ character password.');
      return;
    }
    setState(() {
      _busy = true;
      _msg = null;
    });
    try {
      if (_register) {
        await Data.signUp(_email.text, _pass.text);
        await Data.signIn(_email.text, _pass.text);
      } else {
        await Data.signIn(_email.text, _pass.text);
      }
      // AuthGate's stream navigates on success.
    } catch (e) {
      setState(() => _msg = e.toString().replaceAll('AuthException:', '').trim());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 24),
                const Text('⚡ OPPORTA',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                        color: Brand.text,
                        fontSize: 30,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 2)),
                const SizedBox(height: 6),
                const Text('Every Opportunity. One Platform.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Brand.muted, fontSize: 13)),
                const SizedBox(height: 8),
                const Text('CG + UP government tenders & jobs',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Brand.cyan, fontSize: 12)),
                const SizedBox(height: 36),
                Row(children: [
                  Expanded(
                      child: _modeTab('Login', !_register,
                          () => setState(() => _register = false))),
                  const SizedBox(width: 8),
                  Expanded(
                      child: _modeTab('Register', _register,
                          () => setState(() => _register = true))),
                ]),
                const SizedBox(height: 18),
                TextField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(hintText: 'you@gmail.com')),
                const SizedBox(height: 12),
                TextField(
                    controller: _pass,
                    obscureText: true,
                    decoration:
                        const InputDecoration(hintText: 'Password (min 6 chars)')),
                if (_msg != null) ...[
                  const SizedBox(height: 12),
                  Text(_msg!,
                      style: const TextStyle(color: Brand.amber, fontSize: 13)),
                ],
                const SizedBox(height: 18),
                FilledButton(
                    onPressed: _busy ? null : _submit,
                    child: _busy
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : Text(_register ? 'Create account' : 'Login')),
                const SizedBox(height: 14),
                const Text('Signup is instant — no verification code needed.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Brand.muted, fontSize: 12)),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _modeTab(String label, bool active, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: active ? Brand.cyan : Brand.surface2,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Brand.border),
        ),
        child: Text(label,
            textAlign: TextAlign.center,
            style: TextStyle(
                color: active ? const Color(0xFF02040A) : Brand.text,
                fontWeight: FontWeight.w700)),
      ),
    );
  }
}
