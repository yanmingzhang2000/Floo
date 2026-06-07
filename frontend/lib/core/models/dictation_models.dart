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
  final int dictationId;
  final double accuracyRate; // 0-100
  final int earnedPoints;
  final int reviewStage;
  final DateTime? nextReviewAt;
  final DictationFeedback feedback;

  DictationResult({
    required this.dictationId,
    required this.accuracyRate,
    required this.earnedPoints,
    required this.reviewStage,
    this.nextReviewAt,
    required this.feedback,
  });

  // 前端显示用，accuracy_rate 即为分数（0-100）
  int get score => accuracyRate.round();
  int get accuracy => accuracyRate.round();

  factory DictationResult.fromJson(Map<String, dynamic> json) {
    return DictationResult(
      dictationId: json['dictation_id'] as int,
      accuracyRate: (json['accuracy_rate'] as num?)?.toDouble() ?? 0.0,
      earnedPoints: json['earned_points'] as int? ?? 0,
      reviewStage: json['review_stage'] as int? ?? 1,
      nextReviewAt: json['next_review_at'] != null
          ? DateTime.parse(json['next_review_at'] as String)
          : null,
      feedback: DictationFeedback.fromJson(
        json['feedback'] as Map<String, dynamic>,
      ),
    );
  }
}

class DictationHistory {
  final int dictationId;
  final int? contentId;
  final double accuracyRate;
  final int earnedPoints;
  final DateTime createdAt;

  DictationHistory({
    required this.dictationId,
    this.contentId,
    required this.accuracyRate,
    required this.earnedPoints,
    required this.createdAt,
  });

  int get score => accuracyRate.round();

  factory DictationHistory.fromJson(Map<String, dynamic> json) {
    return DictationHistory(
      dictationId: json['dictation_id'] as int,
      contentId: json['content_id'] as int?,
      accuracyRate: (json['accuracy_rate'] as num?)?.toDouble() ?? 0.0,
      earnedPoints: json['earned_points'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}