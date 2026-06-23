import 'package:flutter/material.dart';
import '../config.dart';
import 'tenders.dart';
import 'jobs.dart';
import 'profile.dart';
import 'analytics.dart';

/// Bottom-nav shell: Profile · Tenders · Jobs · Analytics (matches the web order).
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _i = 1; // default to Tenders
  final _pages = const [
    ProfileScreen(),
    TendersScreen(),
    JobsScreen(),
    AnalyticsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(child: _pages[_i]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _i,
        backgroundColor: Brand.surface,
        indicatorColor: Brand.cyan.withOpacity(0.18),
        onDestinationSelected: (v) => setState(() => _i = v),
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person, color: Brand.cyan),
              label: 'Profile'),
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
        ],
      ),
    );
  }
}
