// Android/iOS implementation of the alert scheduler (see notifications.dart).
import 'dart:io' show Platform;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;
import 'data.dart';

final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
bool _ready = false;

const _channelId = 'opporta_alerts';

Future<void> initImpl() async {
  if (!(Platform.isAndroid || Platform.isIOS)) return;
  if (_ready) return;
  tzdata.initializeTimeZones();
  // CG/UP users are all in India — fixed IST avoids an extra timezone plugin.
  try {
    tz.setLocalLocation(tz.getLocation('Asia/Kolkata'));
  } catch (_) {}

  const android = AndroidInitializationSettings('@mipmap/ic_launcher');
  const ios = DarwinInitializationSettings();
  await _plugin.initialize(
    const InitializationSettings(android: android, iOS: ios),
  );
  _ready = true;
}

Future<void> syncAlertsImpl() async {
  if (!_ready || !Data.signedIn) return;

  // Ask for permission (Android 13+ / iOS). Idempotent — no dialog if granted.
  final android = _plugin.resolvePlatformSpecificImplementation<
      AndroidFlutterLocalNotificationsPlugin>();
  await android?.requestNotificationsPermission();
  final ios = _plugin.resolvePlatformSpecificImplementation<
      IOSFlutterLocalNotificationsPlugin>();
  await ios?.requestPermissions(alert: true, badge: true, sound: true);

  // Rebuild the whole schedule from current data.
  await _plugin.cancelAll();
  final now = DateTime.now();
  int id = 1;

  final profile = await Data.profile();
  final tenders = await Data.tenders();
  final docs = await Data.documents();

  // 1) Deadline alerts — eligible tenders closing within 7 days.
  for (final t in tenders) {
    if (id > 30) break;
    final dl = t.daysLeft;
    if (dl == null || dl < 0 || dl > 7) continue;
    if (Eligibility.verdict(t, profile) != 'ELIGIBLE') continue;
    final deadline = DateTime.tryParse(t.deadline);
    if (deadline == null) continue;
    // Fire 2 days before the deadline at 9am; if that's past, fire ~2h from now.
    var when = DateTime(deadline.year, deadline.month, deadline.day, 9)
        .subtract(const Duration(days: 2));
    if (when.isBefore(now)) when = now.add(const Duration(hours: 2));
    await _schedule(
      id++,
      '⏱ Tender closing soon',
      '${t.title} • closes in ${dl}d (${t.org})',
      when,
    );
  }

  // 2) Document-expiry alerts — vault docs expiring within 30 days.
  for (final d in docs) {
    if (id > 60) break;
    final exp = DateTime.tryParse('${d['expiry_date'] ?? ''}');
    if (exp == null) continue;
    final days = exp.difference(now).inDays;
    if (days < 0 || days > 30) continue;
    final name = '${d['name'] ?? d['doc_type'] ?? 'Document'}';
    // Remind 7 days before expiry at 9am; else soon.
    var when = DateTime(exp.year, exp.month, exp.day, 9)
        .subtract(const Duration(days: 7));
    if (when.isBefore(now)) when = now.add(const Duration(hours: 3));
    await _schedule(
      id++,
      '📄 Document expiring',
      '$name expires in ${days}d — renew it to stay eligible',
      when,
    );
  }
}

Future<void> _schedule(int id, String title, String body, DateTime when) async {
  const details = NotificationDetails(
    android: AndroidNotificationDetails(
      _channelId,
      'Opporta Alerts',
      channelDescription: 'Tender deadlines & document-expiry reminders',
      importance: Importance.high,
      priority: Priority.high,
    ),
    iOS: DarwinNotificationDetails(),
  );
  try {
    await _plugin.zonedSchedule(
      id,
      title,
      body,
      tz.TZDateTime.from(when, tz.local),
      details,
      // Interpret the scheduled time as an absolute instant (iOS requirement).
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      // Inexact => no SCHEDULE_EXACT_ALARM permission (no Play Store policy form).
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
    );
  } catch (_) {
    // Permission denied or scheduling unavailable — fail quietly.
  }
}
