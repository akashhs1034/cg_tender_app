import 'package:flutter/material.dart';
import '../config.dart';
import '../notifications.dart';
import 'dashboard.dart';
import 'tenders.dart';
import 'jobs.dart';
import 'profile.dart';
import 'analytics.dart';

/// Bottom-nav shell: Home · Tenders · Jobs · Analytics · Profile. The Home hub
/// surfaces everything else (Explore, Bid Workshop, Study Matrix, Alerts,
/// Portals) so the full web feature set is one or two taps away.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _i = 0; // default to Home / Dashboard
  final _pages = const [
    DashboardScreen(),
    TendersScreen(),
    JobsScreen(),
    AnalyticsScreen(),
    ProfileScreen(),
  ];

  @override
  void initState() {
    super.initState();
    // Reschedule deadline / doc-expiry alerts from live data on each app open.
    // Fire-and-forget — syncAlerts is idempotent and never throws.
    Notifications.syncAlerts();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(child: _pages[_i]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _i,
        backgroundColor: Brand.surface,
        indicatorColor: Brand.cyan.withValues(alpha: 0.18),
        onDestinationSelected: (v) => setState(() => _i = v),
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home, color: Brand.cyan),
              label: 'Home'),
          NavigationDestination(
              icon: Icon(Icons.description_outlined),
              selectedIcon: Icon(Icons.description, color: Brand.cyan),
              label: 'Tenders'),
          NavigationDestination(
              icon: Icon(Icons.work_outline),
              selectedIcon: Icon(Icons.work, color: Brand.cyan),
              label: 'Jobs'),
          NavigationDestination(
              icon: Icon(Icons.bar_chart_outlined),
              selectedIcon: Icon(Icons.bar_chart, color: Brand.cyan),
              label: 'Analytics'),
          NavigationDestination(
              icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person, color: Brand.cyan),
              label: 'Profile'),
        ],
      ),
    );
  }
}
