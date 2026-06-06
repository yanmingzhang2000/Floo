import 'dart:convert';

// 学习内容相关模型

class LearningContent {
  final int id;
  final int creatorType; // 0=AI, 1=user
  final String difficultyLevel;
  final String themeType;
  final String title;
  final String article;
  final String? translation;
  final List<String> keyWords;
  final DateTime contentDate;

  LearningContent({
    required this.id,
    required this.creatorType,
    required this.difficultyLevel,
    required this.themeType,
    required this.title,
    required this.article,
    this.translation,
    required this.keyWords,
    required this.contentDate,
  });

  factory LearningContent.fromJson(Map<String, dynamic> json) {
    // 后端字段名映射
    final id = (json['id'] ?? json['content_id']) as int;
    final article = (json['article'] ?? json['content_text']) as String;
    final contentDateStr = (json['content_date'] ?? json['created_at']) as String;

    // key_words 可能是 JSON 字符串或数组
    List<String> words = [];
    final kwField = json['key_words'];
    if (kwField is String) {
      try {
        final decoded = jsonDecode(kwField);
        if (decoded is List) words = decoded.map((e) => e.toString()).toList();
      } catch (_) {}
    } else if (kwField is List) {
      words = kwField.map((e) => e.toString()).toList();
    }

    return LearningContent(
      id: id,
      creatorType: json['creator_type'] as int? ?? 0,
      difficultyLevel: json['difficulty_level'] as String? ?? 'medium',
      themeType: json['theme_type'] as String? ?? 'mixed',
      title: json['title'] as String,
      article: article,
      translation: json['translation'] as String?,
      keyWords: words,
      contentDate: DateTime.parse(contentDateStr),
    );
  }
}

class ReviewTask {
  final int progressId;
  final int contentId;
  final String title;
  final int reviewStage;
  final DateTime nextReviewAt;

  ReviewTask({
    required this.progressId,
    required this.contentId,
    required this.title,
    required this.reviewStage,
    required this.nextReviewAt,
  });

  factory ReviewTask.fromJson(Map<String, dynamic> json) {
    return ReviewTask(
      progressId: json['progress_id'] as int,
      contentId: json['content_id'] as int,
      title: json['title'] as String,
      reviewStage: json['review_stage'] as int,
      nextReviewAt: DateTime.parse(json['next_review_at'] as String),
    );
  }
}

class WeeklySummary {
  final int summaryId;
  final int userId;
  final int yearWeek;
  final int checkinCount;
  final int dictationCount;
  final int avgAccuracy;
  final int totalPoints;

  WeeklySummary({
    required this.summaryId,
    required this.userId,
    required this.yearWeek,
    required this.checkinCount,
    required this.dictationCount,
    required this.avgAccuracy,
    required this.totalPoints,
  });

  factory WeeklySummary.fromJson(Map<String, dynamic> json) {
    return WeeklySummary(
      summaryId: json['summary_id'] as int,
      userId: json['user_id'] as int,
      yearWeek: json['year_week'] as int,
      checkinCount: json['checkin_count'] as int? ?? 0,
      dictationCount: json['dictation_count'] as int? ?? 0,
      avgAccuracy: json['avg_accuracy'] as int? ?? 0,
      totalPoints: json['total_points'] as int? ?? 0,
    );
  }

  String get weekDisplay {
    final year = yearWeek ~/ 100;
    final week = yearWeek % 100;
    return '$year年第$week周';
  }
}