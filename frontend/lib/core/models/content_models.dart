// 学习内容相关模型

/// 词汇条目，对应后端 lexicon 词条
class WordItem {
  final String word;
  final String phonetic;
  final String meaning;
  final String usage;
  final bool isLongWord;

  const WordItem({
    required this.word,
    required this.phonetic,
    required this.meaning,
    required this.usage,
    required this.isLongWord,
  });

  factory WordItem.fromJson(Map<String, dynamic> json) {
    return WordItem(
      word: json['word'] as String? ?? '',
      phonetic: json['phonetic'] as String? ?? '',
      meaning: json['meaning'] as String? ?? '',
      usage: json['usage'] as String? ?? '',
      isLongWord: json['is_long_word'] as bool? ?? false,
    );
  }
}

/// 今日学习内容列表（总览 + 文章）
class TodayContentList {
  final String theme;
  final int dailyGoalMinutes;
  final List<LearningContent> contents;

  TodayContentList({
    required this.theme,
    required this.dailyGoalMinutes,
    required this.contents,
  });

  factory TodayContentList.fromJson(Map<String, dynamic> json) {
    final list = (json['contents'] as List? ?? [])
        .map((e) => LearningContent.fromJson(e as Map<String, dynamic>))
        .toList();
    return TodayContentList(
      theme: json['theme'] as String? ?? '',
      dailyGoalMinutes: json['daily_goal_minutes'] as int? ?? 15,
      contents: list,
    );
  }

  /// 根据学习时长目标决定展示几条内容
  List<LearningContent> get visibleContents {
    if (contents.isEmpty) return [];
    int count;
    if (dailyGoalMinutes < 30) {
      count = 1; // 只看总览
    } else if (dailyGoalMinutes < 40) {
      count = 2; // 总览 + 1 篇
    } else if (dailyGoalMinutes < 50) {
      count = 3; // 总览 + 2 篇
    } else {
      count = 4; // 全部
    }
    return contents.take(count).toList();
  }
}

class LearningContent {
  final int id;
  final String difficultyLevel;
  final String themeType;
  final String title;
  final String article;
  final String? translation;
  final String? audioUrl;  // 存 source_link
  final List<WordItem> words;
  final DateTime contentDate;
  final String contentType;  // overview | article

  LearningContent({
    required this.id,
    required this.difficultyLevel,
    required this.themeType,
    required this.title,
    required this.article,
    this.translation,
    this.audioUrl,
    required this.words,
    required this.contentDate,
    required this.contentType,
  });

  bool get isOverview => contentType == 'overview';

  /// 词汇字符串列表，供文章关键词高亮用
  List<String> get keyWordStrings => words.map((w) => w.word.toLowerCase()).toList();

  factory LearningContent.fromJson(Map<String, dynamic> json) {
    final id = (json['id'] ?? json['content_id']) as int;
    final article = (json['article'] ?? json['content_text']) as String;
    final contentDateStr = (json['content_date'] ?? json['created_at']) as String;

    // 解析 words 列表（后端返回 list of dict）
    final wordsList = (json['words'] as List? ?? [])
        .whereType<Map<String, dynamic>>()
        .map(WordItem.fromJson)
        .toList();

    return LearningContent(
      id: id,
      difficultyLevel: json['difficulty_level'] as String? ?? 'medium',
      themeType: json['theme_type'] as String? ?? 'daily_news',
      title: json['title'] as String,
      article: article,
      translation: json['translation'] as String?,
      audioUrl: json['audio_url'] as String?,
      words: wordsList,
      contentDate: DateTime.parse(contentDateStr),
      contentType: json['content_type'] as String? ?? 'article',
    );
  }
}

class ReviewTask {
  final int contentId;
  final String title;
  final int reviewStage;
  final double lastAccuracy;
  final DateTime nextReviewAt;

  ReviewTask({
    required this.contentId,
    required this.title,
    required this.reviewStage,
    required this.lastAccuracy,
    required this.nextReviewAt,
  });

  factory ReviewTask.fromJson(Map<String, dynamic> json) {
    return ReviewTask(
      contentId: json['content_id'] as int,
      title: json['title'] as String,
      reviewStage: json['review_stage'] as int,
      lastAccuracy: (json['last_accuracy'] as num?)?.toDouble() ?? 0.0,
      nextReviewAt: DateTime.parse(json['next_review_at'] as String),
    );
  }
}

class WeeklySummary {
  final String yearWeek;         // 格式 YYYYWW
  final int totalCheckinDays;
  final int totalLearnedCount;
  final double avgAccuracyRate;
  final int totalEarnedPoints;
  final int weeklyReviewStatus;

  WeeklySummary({
    required this.yearWeek,
    required this.totalCheckinDays,
    required this.totalLearnedCount,
    required this.avgAccuracyRate,
    required this.totalEarnedPoints,
    required this.weeklyReviewStatus,
  });

  factory WeeklySummary.fromJson(Map<String, dynamic> json) {
    return WeeklySummary(
      yearWeek: json['year_week'] as String? ?? '',
      totalCheckinDays: json['total_checkin_days'] as int? ?? 0,
      totalLearnedCount: json['total_learned_count'] as int? ?? 0,
      avgAccuracyRate: (json['avg_accuracy_rate'] as num?)?.toDouble() ?? 0.0,
      totalEarnedPoints: json['total_earned_points'] as int? ?? 0,
      weeklyReviewStatus: json['weekly_review_status'] as int? ?? 0,
    );
  }

  String get weekDisplay {
    // yearWeek 格式 202623 → 2026年第23周
    if (yearWeek.length == 6) {
      final year = yearWeek.substring(0, 4);
      final week = int.tryParse(yearWeek.substring(4)) ?? 0;
      return '$year年第$week周';
    }
    return yearWeek;
  }
}