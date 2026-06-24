// On-device alert scheduler facade.
//
// Why on-device (not FCM): the app already loads every tender deadline and
// every document `expiry_date`, so we can schedule the exact reminders the user
// asked for with ZERO server / Firebase setup. The OS fires these even when the
// app is closed (they're real alarms), and we refresh the schedule on each open.
// True server-push (for users who never open the app for weeks) can be layered
// on later via FCM + a device-token table — see README.
//
// The real implementation pulls in flutter_local_notifications + timezone, which
// are Android/iOS-only. The conditional import swaps in a no-op stub on web so
// `flutter build web` never compiles those plugins.
import 'notifications_native.dart'
    if (dart.library.html) 'notifications_stub.dart' as impl;

class Notifications {
  /// Initialise the plugin + timezone db. Call once at startup (after Supabase).
  static Future<void> init() => impl.initImpl();

  /// Request permission (idempotent) and (re)schedule deadline + expiry alerts
  /// from the signed-in user's live tenders + documents. Safe to call on every
  /// app open / pull-to-refresh.
  static Future<void> syncAlerts() => impl.syncAlertsImpl();
}
