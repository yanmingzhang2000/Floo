import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/models/checkin_models.dart';
import '../../core/models/content_models.dart';
import '../../core/providers/auth_provider.dart';

class CalendarParams {
  final int year;
  final int month;
  const CalendarParams(this.year, this.month);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CalendarParams && other.year == year && other.month == month);

  @override
  int get hashCode => Object.hash(year, month);
}

// 当前查看的月份
final currentMonthProvider = StateProvider<CalendarParams>((ref) {
  final now = DateTime.now();
  return CalendarParams(now.year, now.month);
});

// 打卡日历数据
final calendarProvider = FutureProvider.autoDispose<CheckinCalendar>((ref) async {
  final p = ref.watch(currentMonthProvider);
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  final resp = await dio.get('/api/checkin/calendar', queryParameters: {
    'user_id': userId,
    'year': p.year,
    'month': p.month,
  });
  return CheckinCalendar.fromJson(resp.data as Map<String, dynamic>);
});

// 执行今日打卡
final doCheckinProvider = FutureProvider.autoDispose<CheckinRecord>((ref) async {
  final dio = ref.read(dioProvider);
  final userId = ref.read(currentUserIdProvider);
  final resp = await dio.post('/api/checkin', data: {'user_id': userId});
  return CheckinRecord.fromJson(resp.data as Map<String, dynamic>);
});

// 每周总结
final weeklySummaryProvider = FutureProvider.autoDispose<WeeklySummary>((ref) async {
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  final resp = await dio.get('/api/checkin/weekly', queryParameters: {'user_id': userId});
  return WeeklySummary.fromJson(resp.data as Map<String, dynamic>);
});