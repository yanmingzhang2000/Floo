// 打卡相关模型

class CheckinCalendar {
  final int year;
  final int month;
  final List<DateTime> checkedDates;
  final int currentStreakDays;
  final int availablePoints;

  CheckinCalendar({
    required this.year,
    required this.month,
    required this.checkedDates,
    required this.currentStreakDays,
    required this.availablePoints,
  });

  factory CheckinCalendar.fromJson(Map<String, dynamic> json) {
    return CheckinCalendar(
      year: json['year'] as int,
      month: json['month'] as int,
      checkedDates: ((json['checked_dates'] as List?) ?? [])
          .map((e) => DateTime.parse(e as String))
          .toList(),
      currentStreakDays: json['current_streak_days'] as int? ?? 0,
      availablePoints: json['available_points'] as int? ?? 0,
    );
  }
}

class CheckinRecord {
  final int checkinId;
  final int userId;
  final DateTime checkinDate;
  final int pointsEarned;
  final int streakDays;

  CheckinRecord({
    required this.checkinId,
    required this.userId,
    required this.checkinDate,
    required this.pointsEarned,
    required this.streakDays,
  });

  factory CheckinRecord.fromJson(Map<String, dynamic> json) {
    return CheckinRecord(
      checkinId: json['checkin_id'] as int,
      userId: json['user_id'] as int,
      checkinDate: DateTime.parse(json['checkin_date'] as String),
      pointsEarned: json['points_earned'] as int? ?? 0,
      streakDays: json['streak_days'] as int? ?? 0,
    );
  }
}