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

// 打卡响应（包含打卡记录 + 积分 + 连续天数）
class CheckinResponse {
  final int currentStreakDays;
  final int availablePoints;
  final int pointsEarned;

  CheckinResponse({
    required this.currentStreakDays,
    required this.availablePoints,
    required this.pointsEarned,
  });

  factory CheckinResponse.fromJson(Map<String, dynamic> json) {
    final checkin = json['checkin'] as Map<String, dynamic>? ?? {};
    return CheckinResponse(
      currentStreakDays: json['current_streak_days'] as int? ?? 0,
      availablePoints: json['available_points'] as int? ?? 0,
      pointsEarned: checkin['earned_points'] as int? ?? 0,
    );
  }
}

// 执行今日打卡
final doCheckinProvider = FutureProvider.autoDispose<CheckinResponse>((ref) async {
  final dio = ref.read(dioProvider);
  final userId = ref.read(currentUserIdProvider);
  final resp = await dio.post('/api/checkin', data: {'user_id': userId});
  return CheckinResponse.fromJson(resp.data as Map<String, dynamic>);
});

// 每周总结（404 表示本周暂无数据，返回空对象而不是抛错）
final weeklySummaryProvider = FutureProvider.autoDispose<WeeklySummary?>((ref) async {
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  try {
    final resp = await dio.get('/api/checkin/weekly', queryParameters: {'user_id': userId});
    return WeeklySummary.fromJson(resp.data as Map<String, dynamic>);
  } catch (e) {
    // 本周暂无数据时后端返回 404，前端显示空状态
    if (e.toString().contains('404')) return null;
    rethrow;
  }
});