// 用户相关模型

class UserProfile {
  final int userId;
  final String username;
  final String? nickname;
  final int currentPoints;
  final int totalPoints;
  final int currentStreakDays;
  final int maxStreakDays;

  UserProfile({
    required this.userId,
    required this.username,
    this.nickname,
    required this.currentPoints,
    required this.totalPoints,
    required this.currentStreakDays,
    required this.maxStreakDays,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      userId: json['user_id'] as int,
      username: json['username'] as String,
      nickname: json['nickname'] as String?,
      currentPoints: json['current_points'] as int? ?? 0,
      totalPoints: json['total_points'] as int? ?? 0,
      currentStreakDays: json['current_streak_days'] as int? ?? 0,
      maxStreakDays: json['max_streak_days'] as int? ?? 0,
    );
  }
}

class UserPreference {
  final String difficultyLevel; // easy, medium, hard
  final String themeType; // tech, business, culture, daily, mixed
  final int dailyGoalMinutes;

  UserPreference({
    required this.difficultyLevel,
    required this.themeType,
    required this.dailyGoalMinutes,
  });

  factory UserPreference.fromJson(Map<String, dynamic> json) {
    return UserPreference(
      difficultyLevel: json['difficulty_level'] as String? ?? 'medium',
      themeType: json['theme_type'] as String? ?? 'mixed',
      dailyGoalMinutes: json['daily_goal_minutes'] as int? ?? 15,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'difficulty_level': difficultyLevel,
      'theme_type': themeType,
      'daily_goal_minutes': dailyGoalMinutes,
    };
  }
}

class PointAccount {
  final int userId;
  final int currentBalance;
  final int totalEarned;
  final int totalSpent;

  PointAccount({
    required this.userId,
    required this.currentBalance,
    required this.totalEarned,
    required this.totalSpent,
  });

  factory PointAccount.fromJson(Map<String, dynamic> json) {
    return PointAccount(
      userId: json['user_id'] as int,
      currentBalance: json['current_balance'] as int? ?? 0,
      totalEarned: json['total_earned'] as int? ?? 0,
      totalSpent: json['total_spent'] as int? ?? 0,
    );
  }
}

class PointTransaction {
  final int logId;
  final int userId;
  final String changeType; // earn, spend
  final int amount;
  final String? reason;
  final int balanceAfter;
  final DateTime createdAt;

  PointTransaction({
    required this.logId,
    required this.userId,
    required this.changeType,
    required this.amount,
    this.reason,
    required this.balanceAfter,
    required this.createdAt,
  });

  factory PointTransaction.fromJson(Map<String, dynamic> json) {
    return PointTransaction(
      logId: json['log_id'] as int,
      userId: json['user_id'] as int,
      changeType: json['change_type'] as String,
      amount: json['amount'] as int,
      reason: json['reason'] as String?,
      balanceAfter: json['balance_after'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}