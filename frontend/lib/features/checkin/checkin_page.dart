import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/models/checkin_models.dart';

import 'checkin_provider.dart';

class CheckinPage extends ConsumerWidget {
  const CheckinPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final params = ref.watch(currentMonthProvider);
    final asyncCal = ref.watch(calendarProvider);
    return Scaffold(
      body: asyncCal.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('加载失败: $e')),
        data: (cal) => _CheckinBody(cal: cal, params: params),
      ),
    );
  }
}

class _CheckinBody extends ConsumerWidget {
  final CheckinCalendar cal;
  final CalendarParams params;
  const _CheckinBody({required this.cal, required this.params});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 120,
          pinned: true,
                    backgroundColor: cs.primary,
          flexibleSpace: FlexibleSpaceBar(
            title: Text('打卡日历',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
            background: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [cs.primary, cs.primaryContainer],
                ),
              ),
            ),
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.all(16),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _StreakBanner(cal: cal),
              const SizedBox(height: 16),
              _CalendarCard(cal: cal, params: params),
              const SizedBox(height: 16),
              _CheckinButton(cal: cal),const SizedBox(height: 16),
              _WeeklyEntryCard(),
              const SizedBox(height: 24),
            ]),
          ),
        ),
      ],
    );
  }
}

class _StreakBanner extends StatelessWidget {
  final CheckinCalendar cal;
  const _StreakBanner({required this.cal});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
        return Card(
      color: cs.secondaryContainer.withValues(alpha: 0.5),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Row(
          children: [
                        _StatItem(icon: Icons.local_fire_department, iconColor: Colors.orange,
                value: '${cal.currentStreakDays}', label: '连续打卡天数'),
            Container(width: 1, height: 48, color: cs.onSurface.withValues(alpha: 0.15)),
                    _StatItem(icon: Icons.calendar_today, iconColor: Colors.blue,
                        value: '${cal.checkedDates.length}', label: '本月打卡'),
                    Container(width: 1, height: 48, color: cs.onSurface.withValues(alpha: 0.15)),
            _StatItem(icon: Icons.stars_rounded, iconColor: Colors.yellow.shade700,
                value: '${cal.availablePoints}', label: '可用积分'),
          ],
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String value;
  final String label;
  const _StatItem({required this.icon, required this.iconColor, required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Expanded(
      child: Column(
        children: [
          Icon(icon, color: iconColor, size: 26),
          const SizedBox(height: 4),
                    Text(value,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: cs.onSurface,
                  )),
          Text(label, style: TextStyle(fontSize: 10, color: cs.onSurfaceVariant)),
        ],
      ),
    );
  }
}

class _CalendarCard extends ConsumerWidget {
  final CheckinCalendar cal;
  final CalendarParams params;
  const _CalendarCard({required this.cal, required this.params});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    final firstDay = DateTime(cal.year, cal.month, 1);
    final daysInMonth = DateTime(cal.year, cal.month + 1, 0).day;
    final leadingBlanks = firstDay.weekday % 7;
    final today = DateTime.now();
    final checked = cal.checkedDates
        .map((d) => '${d.year}-${d.month}-${d.day}')
        .toSet();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // 月份导航
            Row(
              children: [
                IconButton(
                    onPressed: () => _shift(ref, -1),
                    icon: const Icon(Icons.chevron_left)),
                Expanded(
                  child: Center(
                    child: Text('${params.year} 年 ${params.month} 月',
                        style: Theme.of(context).textTheme.titleMedium),
                  ),
                ),
                IconButton(
                    onPressed: () => _shift(ref, 1),
                    icon: const Icon(Icons.chevron_right)),
              ],
            ),
            const SizedBox(height: 8),
            // 星期标题
            GridView.count(
              crossAxisCount: 7,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: ['日', '一', '二', '三', '四', '五', '六']
                  .map((w) => Center(
                        child: Text(w,
                            style: TextStyle(
                                color: cs.onSurfaceVariant,
                                fontWeight: FontWeight.w600,
                                fontSize: 12)),
                      ))
                  .toList(),
            ),
            // 日期格子
            GridView.count(
              crossAxisCount: 7,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 4,
              crossAxisSpacing: 4,
              children: [
                ...List.generate(leadingBlanks, (_) => const SizedBox.shrink()),
                ...List.generate(daysInMonth, (i) {
                  final day = i + 1;
                  final date = DateTime(cal.year, cal.month, day);
                  final isChecked = checked.contains('${date.year}-${date.month}-${date.day}');
                  final isToday = date.year == today.year &&
                      date.month == today.month &&
                      date.day == today.day;
                  final bg = isChecked
                      ? cs.primary
                      : (isToday ? cs.secondaryContainer : cs.surfaceContainerHighest);
                  final fg = isChecked
                      ? cs.onPrimary
                      : (isToday ? cs.onSecondaryContainer : cs.onSurface);
                  return Container(
                    decoration: BoxDecoration(
                      color: bg,
                      borderRadius: BorderRadius.circular(8),
                      border: isToday && !isChecked
                          ? Border.all(color: cs.primary, width: 1.5)
                          : null,
                    ),
                    alignment: Alignment.center,
                    child: isChecked
                        ? Icon(Icons.check, size: 16, color: fg)
                        : Text('$day',
                            style: TextStyle(
                                color: fg,
                                fontWeight: FontWeight.w600,
                                fontSize: 12)),
                  );
                }),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _shift(WidgetRef ref, int delta) {
    final cur = ref.read(currentMonthProvider);
    final d = DateTime(cur.year, cur.month + delta, 1);
    ref.read(currentMonthProvider.notifier).state = CalendarParams(d.year, d.month);
  }
}

class _CheckinButton extends ConsumerWidget {
  final CheckinCalendar cal;
  const _CheckinButton({required this.cal});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final today = DateTime.now();
    final alreadyChecked = cal.checkedDates.any((d) =>
        d.year == today.year && d.month == today.month && d.day == today.day);

    return FilledButton.icon(
      icon: Icon(alreadyChecked ? Icons.check_circle : Icons.check_circle_outline),
      label: Text(alreadyChecked ? '今日已打卡 ✓' : '今日打卡'),
      style: alreadyChecked
          ? FilledButton.styleFrom(backgroundColor: Colors.green.shade600)
          : null,
      onPressed: alreadyChecked
          ? null
          : () async {
              final messenger = ScaffoldMessenger.of(context);
                            try {
                final result = await ref.refresh(doCheckinProvider.future);
                ref.invalidate(calendarProvider);
                messenger.showSnackBar(SnackBar(
                    content: Text('打卡成功！连续 ${result.currentStreakDays} 天，+${result.pointsEarned} 积分 🎉')));
              } catch (e) {
                messenger.showSnackBar(SnackBar(content: Text('打卡失败: $e')));
              }
            },
    );
  }
}

class _WeeklyEntryCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: cs.tertiaryContainer,
          child: Icon(Icons.bar_chart, color: cs.tertiary),
        ),
        title: const Text('每周学习报告', style: TextStyle(fontWeight: FontWeight.w600)),
        subtitle: const Text('查看本周打卡、默写、积分统计'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push('/weekly'),
      ),
    );
  }
}