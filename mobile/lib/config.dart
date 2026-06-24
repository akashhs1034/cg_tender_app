import 'package:flutter/material.dart';

/// Supabase client config. The anon (publishable) key is SAFE to ship in a
/// client app — Row Level Security on the database is what protects user data.
/// NEVER put the service_role key here.
class Config {
  static const supabaseUrl = 'https://iujzepmdnkawbmpupuzk.supabase.co';
  // Publishable key (sb_publishable_) — safe to ship; independent of the legacy
  // JWT keys, so disabling the exposed legacy anon/service_role keys won't break
  // the app. RLS still protects all user data.
  static const supabaseAnonKey = 'sb_publishable_CmCGeCp_QlqseKtf8XaX9w_NSOt2vKe';
}

/// Opporta brand palette (mirrors the web app: obsidian + cyan/blue).
class Brand {
  static const bg       = Color(0xFF02040A);
  static const surface  = Color(0xFF080F22);
  static const surface2 = Color(0xFF040E22);
  static const cyan     = Color(0xFF00C4FF);
  static const blue     = Color(0xFF1B6CF7);
  static const green    = Color(0xFF10B981);
  static const amber    = Color(0xFFF59E0B);
  static const red      = Color(0xFFF87171);
  static const text     = Color(0xFFE2E8F0);
  static const muted    = Color(0xFF7C8AA0);
  static const border   = Color(0x1A00C4FF);

  static ThemeData theme() {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: bg,
      colorScheme: const ColorScheme.dark(
        primary: cyan, secondary: blue, surface: surface, error: red),
      appBarTheme: const AppBarTheme(
        backgroundColor: bg, elevation: 0, centerTitle: false,
        titleTextStyle: TextStyle(
          color: text, fontSize: 18, fontWeight: FontWeight.w800)),
      cardTheme: CardThemeData(
        color: surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: border)),
        margin: const EdgeInsets.symmetric(vertical: 6)),
      inputDecorationTheme: InputDecorationTheme(
        filled: true, fillColor: surface2,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: border)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: border))),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: cyan, foregroundColor: const Color(0xFF02040A),
          minimumSize: const Size.fromHeight(48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12)))),
    );
  }
}
