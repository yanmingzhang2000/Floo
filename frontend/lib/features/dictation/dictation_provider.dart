import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/models/dictation_models.dart';
import '../../core/providers/auth_provider.dart';

// 提交状态
class DictationState {
  final bool loading;
  final DictationResult? result;
  final String? error;

  const DictationState({this.loading = false, this.result, this.error});

  DictationState copyWith({
    bool? loading,
    DictationResult? result,
    String? error,
    bool clearResult = false,
    bool clearError = false,
  }) {
    return DictationState(
      loading: loading ?? this.loading,
      result: clearResult ? null : (result ?? this.result),
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class DictationController extends StateNotifier<DictationState> {
  DictationController(this.ref) : super(const DictationState());
  final Ref ref;

  // 提交默写，不再从客户端传 original_text
  Future<void> submit({required int contentId, required String userInput}) async {
    state = state.copyWith(loading: true, clearError: true, clearResult: true);
    try {
      final dio = ref.read(dioProvider);
      final userId = ref.read(currentUserIdProvider);
      final resp = await dio.post('/api/dictation/submit', data: {
        'user_id': userId,
        'content_id': contentId,
        'user_input': userInput,
      });
      final result = DictationResult.fromJson(resp.data as Map<String, dynamic>);
      state = state.copyWith(loading: false, result: result);
    } catch (e) {
      state = state.copyWith(loading: false, error: _parseError(e));
    }
  }

  void reset() => state = const DictationState();

  String _parseError(Object e) {
    final s = e.toString();
    if (s.contains('404')) return '未找到对应内容，请先生成今日学习内容';
    if (s.contains('connection') || s.contains('SocketException')) return '网络连接失败';
    return '提交失败，请稍后重试';
  }
}

final dictationControllerProvider =
    StateNotifierProvider<DictationController, DictationState>(
  (ref) => DictationController(ref),
);

// 听写历史记录
final dictationHistoryProvider = FutureProvider<List<DictationHistory>>((ref) async {
  final dio = ref.watch(dioProvider);
  final userId = ref.watch(currentUserIdProvider);
  final resp = await dio.get('/api/dictation/history', queryParameters: {'user_id': userId});
  final list = resp.data as List? ?? [];
  return list.map((e) => DictationHistory.fromJson(e as Map<String, dynamic>)).toList();
});