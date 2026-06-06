// 听写相关模型

class DictationDiff {
  final String type; // missing / wrong / extra
  final String expected;
  final String actual;

  DictationDiff({
    required this.type,
    required this.expected,
    required this.actual,
  });

  factory DictationDiff.fromJson(Map<String, dynamic> json) {
    return DictationDiff(
      type: json['type'] as String? ?? '',
      expected: json['expected'] as String? ?? '',
      actual: json['actual'] as String? ?? '',
    );
  }
}

class DictationFeedback {
  final int score;
  final String summary;
  final List<DictationDiff> diffs;
  final List<String> suggestions;

  DictationFeedback({
    required this.score,
    required this.summary,
    required this.diffs,
    required this.suggestions,
  });

  factory DictationFeedback.fromJson(Map<String, dynamic> json) {
    return DictationFeedback(
      score: json['score'] as int? ?? 0,
      summary: json['summary'] as String? ?? '',
      diffs: ((json['diffs'] as List?) ?? [])
          .map((e) => DictationDiff.fromJson(e as Map<String, dynamic>))
          .toList(),
      suggestions: ((json['suggestions'] as List?) ?? [])
          .map((e) => e.toString())
          .toList(),
    );
  }
}

class DictationResult {
  final int recordId;
  final int contentId;
  final int score;
  final int accuracy;
  final int earnedPoints;
  final int reviewStage;
  final DateTime nextReviewAt;
  final DictationFeedback feedback;

  DictationResult({
    required this.recordId,
    required this.contentId,
    required this.score,
    required this.accuracy,
    required this.earnedPoints,
    required this.reviewStage,
    required this.nextReviewAt,
    required this.feedback,
  });

  factory DictationResult.fromJson(Map<String, dynamic> json) {
    return DictationResult(
      recordId: json['record_id'] as int,
      contentId: json['content_id'] as int,
      score: json['score'] as int? ?? 0,
      accuracy: json['accuracy'] as int? ?? 0,
      earnedPoints: json['earned_points'] as int? ?? 0,
      reviewStage: json['review_stage'] as int? ?? 1,
      nextReviewAt: DateTime.parse(json['next_review_at'] as String),
      feedback: DictationFeedback.fromJson(
        json['feedback'] as Map<String, dynamic>,
      ),
    );
  }
}

class DictationHistory {
  final int recordId;
  final int contentId;
  final String title;
  final int score;
  final int accuracy;
  final int pointsEarned;
  final DateTime submittedAt;

  DictationHistory({
    required this.recordId,
    required this.contentId,
    required this.title,
    required this.score,
    required this.accuracy,
    required this.pointsEarned,
    required this.submittedAt,
  });

  factory DictationHistory.fromJson(Map<String, dynamic> json) {
    return DictationHistory(
      recordId: json['record_id'] as int,
      contentId: json['content_id'] as int,
      title: json['title'] as String? ?? '',
      score: json['score'] as int? ?? 0,
      accuracy: json['accuracy'] as int? ?? 0,
      pointsEarned: json['points_earned'] as int? ?? 0,
      submittedAt: DateTime.parse(json['submitted_at'] as String),
    );
  }
}