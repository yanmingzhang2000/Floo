import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api/api_client.dart';
import '../models/user_models.dart';

// 当前登录用户状态
class AuthState {
  final int? userId;
  final String? username;
  final bool isLoading;
  final String? error;

  const AuthState({
    this.userId,
    this.username,
    this.isLoading = false,
    this.error,
  });

  bool get isLoggedIn => userId != null;

  AuthState copyWith({
    int? userId,
    String? username,
    bool? isLoading,
    String? error,
    bool clearError = false,
    bool logout = false,
  }) {
    return AuthState(
      userId: logout ? null : (userId ?? this.userId),
      username: logout ? null : (username ?? this.username),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this.ref) : super(const AuthState()) {
    _restoreSession();
  }

  final Ref ref;

  Future<void> _restoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getInt('user_id');
    final username = prefs.getString('username');
    if (userId != null && username != null) {
      state = state.copyWith(userId: userId, username: username);
    }
  }

  Future<void> register(String username, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final dio = ref.read(dioProvider);
      final resp = await dio.post('/api/user/register', data: {
        'username': username,
        'password': password,
      });
      final userId = resp.data['user_id'] as int;
      await _saveSession(userId, username);
      state = state.copyWith(isLoading: false, userId: userId, username: username);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _parseError(e));
    }
  }

  Future<void> login(String username, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final dio = ref.read(dioProvider);
      final resp = await dio.post('/api/user/login', data: {
        'username': username,
        'password': password,
      });
      final userId = resp.data['user_id'] as int;
      await _saveSession(userId, username);
      state = state.copyWith(isLoading: false, userId: userId, username: username);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: _parseError(e));
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('user_id');
    await prefs.remove('username');
    state = state.copyWith(logout: true);
  }

  Future<void> _saveSession(int userId, String username) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('user_id', userId);
    await prefs.setString('username', username);
  }

  String _parseError(Object e) {
    final str = e.toString();
    if (str.contains('400')) return '用户名或密码错误';
    if (str.contains('409')) return '用户名已存在';
    if (str.contains('SocketException') || str.contains('connection')) return '网络连接失败';
    return '操作失败，请稍后重试';
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(ref),
);

final currentUserIdProvider = Provider<int>((ref) {
  return ref.watch(authProvider).userId ?? 1;
});

final userPreferenceProvider = FutureProvider.autoDispose<UserPreference>((ref) async {
  final userId = ref.watch(currentUserIdProvider);
  final dio = ref.watch(dioProvider);
  final resp = await dio.get('/api/user/$userId/preference');
  return UserPreference.fromJson(resp.data as Map<String, dynamic>);
});

final pointAccountProvider = FutureProvider.autoDispose<PointAccount>((ref) async {
  final userId = ref.watch(currentUserIdProvider);
  final dio = ref.watch(dioProvider);
  final resp = await dio.get('/api/user/$userId/points');
  return PointAccount.fromJson(resp.data as Map<String, dynamic>);
});