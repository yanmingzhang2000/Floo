import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/login_page.dart';
import '../../features/checkin/checkin_page.dart';
import '../../features/daily/daily_content_detail_page.dart';
import '../../features/daily/daily_list_page.dart';
import '../../features/daily/daily_page.dart';
import '../../features/dictation/dictation_page.dart';
import '../../features/profile/preference_page.dart';
import '../../features/review/review_page.dart';
import '../../features/weekly/weekly_page.dart';
import '../../shared/widgets/nav_scaffold.dart';
import '../providers/auth_provider.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  // 监听登录状态，未登录时重定向到登录页
  final authNotifier = ValueNotifier<AuthState>(ref.read(authProvider));
  ref.listen(authProvider, (_, next) => authNotifier.value = next);

  return GoRouter(
    initialLocation: '/daily',
    refreshListenable: authNotifier,
    redirect: (context, state) {
      final auth = authNotifier.value;
      final isLoginPage = state.matchedLocation == '/login';
      // 未登录且不在登录页 → 跳到登录页
      if (!auth.isLoggedIn && !isLoginPage) return '/login';
      // 已登录但在登录页 → 跳到首页
      if (auth.isLoggedIn && isLoginPage) return '/daily';
      return null;
    },
    routes: [
      // 登录/注册
      GoRoute(path: '/login', builder: (_, __) => const LoginPage()),

      // 主导航 Shell
      ShellRoute(
        builder: (context, state, child) => NavScaffold(
          location: state.matchedLocation,
          child: child,
        ),
        routes: [
          GoRoute(path: '/daily', builder: (_, __) => const DailyPage()),
          GoRoute(path: '/dictation', builder: (_, __) => const DictationPage()),
          GoRoute(path: '/review', builder: (_, __) => const ReviewPage()),
          GoRoute(path: '/checkin', builder: (_, __) => const CheckinPage()),
        ],
      ),

      // 不带底栏的独立页面
      GoRoute(path: '/daily/list', builder: (_, __) => const DailyListPage()),
      GoRoute(
        path: '/daily/content/:id',
        builder: (_, state) {
          final id = int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
          return DailyContentDetailPage(contentId: id);
        },
      ),
      GoRoute(path: '/weekly', builder: (_, __) => const WeeklyPage()),
      GoRoute(path: '/preference', builder: (_, __) => const PreferencePage()),
    ],
  );
});