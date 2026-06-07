import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/models/content_models.dart';
import '../../core/providers/auth_provider.dart';

// 今日学习内容列表（总览 + 文章，按学习时长展示）
final todayListProvider = FutureProvider<TodayContentList>((ref) async {
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  final resp = await dio.get('/api/daily/today-list', queryParameters: {'user_id': userId});
  return TodayContentList.fromJson(resp.data as Map<String, dynamic>);
});

// 今日单条内容（向后兼容，优先返回总览）
final dailyContentProvider = FutureProvider<LearningContent>((ref) async {
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  final resp = await dio.get('/api/daily/today', queryParameters: {'user_id': userId});
  return LearningContent.fromJson(resp.data as Map<String, dynamic>);
});

// AI 生成今日内容（按用户 theme 偏好）
final generateDailyProvider = FutureProvider.autoDispose<int>((ref) async {
  final dio = ref.read(dioProvider);
  final userId = ref.read(currentUserIdProvider);
  final resp = await dio.post('/api/daily/generate', data: {
    'user_id': userId,
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
  try {
    final resp = await dio.get('/api/daily/review', queryParameters: {'user_id': userId});
    final data = resp.data as Map<String, dynamic>;
    final tasks = data['tasks'] as List? ?? [];
    return tasks.map((e) => ReviewTask.fromJson(e as Map<String, dynamic>)).toList();
  } catch (e) {
    // 无复习任务时返回空列表
    if (e.toString().contains('404')) return [];
    rethrow;
  }
});