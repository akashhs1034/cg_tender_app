import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'config.dart';
import 'notifications.dart';
import 'screens/login.dart';
import 'screens/shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Supabase.initialize(
    url: Config.supabaseUrl,
    anonKey: Config.supabaseAnonKey,
  );
  await Notifications.init();
  runApp(const OpportaApp());
}

class OpportaApp extends StatelessWidget {
  const OpportaApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Opporta',
      debugShowCheckedModeBanner: false,
      theme: Brand.theme(),
      home: const AuthGate(),
    );
  }
}

/// Switches between Login and the app shell based on the Supabase session.
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});
  @override
  Widget build(BuildContext context) {
    return StreamBuilder<AuthState>(
      stream: Supabase.instance.client.auth.onAuthStateChange,
      builder: (context, _) {
        final session = Supabase.instance.client.auth.currentSession;
        return session != null ? const HomeShell() : const LoginScreen();
      },
    );
  }
}
