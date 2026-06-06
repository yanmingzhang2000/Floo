import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/models/content_models.dart';
import '../../core/providers/auth_provider.dart';

// 今日学习内容
final dailyContentProvider = FutureProvider<LearningContent>((ref) async {
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  final resp = await dio.get('/api/daily/today', queryParameters: {'user_id': userId});
  return LearningContent.fromJson(resp.data as Map<String, dynamic>);
});

// AI 生成今日内容
final generateDailyProvider = FutureProvider.autoDispose<int>((ref) async {
  final dio = ref.read(dioProvider);
  final userId = ref.read(currentUserIdProvider);
  final pref = await ref.read(userPreferenceProvider.future);
  final resp = await dio.post('/api/daily/generate', data: {
    'user_id': userId,
    'difficulty_override': pref.difficultyLevel,
    'theme_override': pref.themeType,
  });
  return (resp.data['content_id'] as int?) ?? 0;
});

// 历史内容列表
final dailyListProvider = FutureProvider<List<LearningContent>>((ref) async {
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  final resp = await dio.get('/api/daily/list', queryParameters: {'user_id': userId});
  final list = resp.data as List? ?? [];
  return list.map((e) => LearningContent.fromJson(e as Map<String, dynamic>)).toList();
});

// 今日复习任务队列
final reviewListProvider = FutureProvider<List<ReviewTask>>((ref) async {
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  final resp = await dio.get('/api/daily/review', queryParameters: {'user_id': userId});
  final data = resp.data as Map<String, dynamic>;
  final tasks = data['tasks'] as List? ?? [];
  return tasks.map((e) => ReviewTask.fromJson(e as Map<String, dynamic>)).toList();
});