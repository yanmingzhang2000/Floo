import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/auth_provider.dart';

class NavScaffold extends ConsumerWidget {
  final Widget child;
  final String location;
  const NavScaffold({super.key, required this.child, required this.location});

  static const _tabs = [
    ('/daily',     Icons.menu_book_outlined,       Icons.menu_book,       '每日学习'),
    ('/dictation', Icons.edit_note_outlined,        Icons.edit_note,       '听写'),
    ('/review',    Icons.replay_circle_filled_outlined, Icons.replay_circle_filled, '复习'),
    ('/checkin',   Icons.calendar_month_outlined,   Icons.calendar_month,  '打卡'),
  ];

  int get _index {
    final i = _tabs.indexWhere((t) => location.startsWith(t.$1));
    return i < 0 ? 0 : i;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => context.go(_tabs[i].$1),
        destinations: [
          for (final t in _tabs)
            NavigationDestination(
              icon: Icon(t.$2),
              selectedIcon: Icon(t.$3),
              label: t.$4,
            ),
        ],
      ),
      // 右下角个人设置 FAB
      floatingActionButton: FloatingActionButton.small(
        heroTag: 'profile_fab',
        tooltip: '个人设置',
        backgroundColor: cs.surfaceContainerHighest,
        foregroundColor: cs.onSurfaceVariant,
        onPressed: () => _showProfileSheet(context, ref, authState),
        child: const Icon(Icons.person_outline),
      ),
    );
  }

  void _showProfileSheet(BuildContext context, WidgetRef ref, AuthState authState) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => _ProfileSheet(authState: authState, ref: ref),
    );
  }
}

class _ProfileSheet extends StatelessWidget {
  final AuthState authState;
  final WidgetRef ref;
  const _ProfileSheet({required this.authState, required this.ref});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 把手
          Container(
            width: 40, height: 4,
            decoration: BoxDecoration(
              color: cs.onSurfaceVariant.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 16),
          // 用户信息
          CircleAvatar(
            radius: 30,
            backgroundColor: cs.primaryContainer,
            child: Icon(Icons.person, size: 32, color: cs.primary),
          ),
          const SizedBox(height: 8),
          Text(
            authState.username ?? '用户',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 20),
          // 偏好设置
          ListTile(
            leading: CircleAvatar(
              backgroundColor: cs.secondaryContainer,
              child: Icon(Icons.tune, color: cs.secondary),
            ),
            title: const Text('学习偏好设置'),
            subtitle: const Text('难度、主题、每日目标'),
            trailing: const Icon(Icons.chevron_right),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            tileColor: cs.surfaceContainerHighest,
            onTap: () {
              Navigator.pop(context);
              context.push('/preference');
            },
          ),
          const SizedBox(height: 8),
          // 退出登录
          ListTile(
            leading: CircleAvatar(
              backgroundColor: cs.errorContainer,
              child: Icon(Icons.logout, color: cs.error),
            ),
            title: const Text('退出登录'),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            tileColor: cs.surfaceContainerHighest,
            onTap: () async {
              Navigator.pop(context);
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
    );
  }
}