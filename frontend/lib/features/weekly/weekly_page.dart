import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/models/content_models.dart';
import '../checkin/checkin_provider.dart';

class WeeklyPage extends ConsumerWidget {
  const WeeklyPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncSummary = ref.watch(weeklySummaryProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('每周学习报告')),
      body: asyncSummary.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('加载失败: $e')),
        data: (summary) => _SummaryBody(summary: summary),
      ),
    );
  }
}

class _SummaryBody extends StatelessWidget {
  final WeeklySummary summary;
  const _SummaryBody({required this.summary});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // 周标题
        Center(
          child: Text(
            summary.weekDisplay,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
          ),
        ),
        const SizedBox(height: 24),

        // 积分卡
        Card(
          color: cs.primaryContainer,
          child: Padding(padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Icon(Icons.stars_rounded, color: Colors.yellow.shade700, size: 36),
                const SizedBox(width: 12),
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('本周获得积分', style: TextStyle(color: cs.onPrimaryContainer, fontSize: 12)),
                  Text('${summary.totalPoints}',
                      style: Theme.of(context).textTheme.displaySmall?.copyWith(
                            color: cs.onPrimaryContainer, fontWeight: FontWeight.w800)),
                ]),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        // 统计格
        Row(children: [
          Expanded(child: _StatCard(
            icon: Icons.calendar_today,
            iconColor: cs.primary,
            value: '${summary.checkinCount}',
            label: '打卡天数',
            suffix: '/ 7',
          )),
          const SizedBox(width: 12),
          Expanded(child: _StatCard(
            icon: Icons.edit_note,
            iconColor: cs.secondary,
            value: '${summary.dictationCount}',
            label: '默写次数',
          )),
          const SizedBox(width: 12),
          Expanded(child: _StatCard(
            icon: Icons.percent,
            iconColor: summary.avgAccuracy >= 80 ? Colors.green : Colors.orange,
            value: '${summary.avgAccuracy}%',
            label: '平均准确率',
          )),
        ]),
        const SizedBox(height: 24),

        // 激励语
        _MotivationCard(summary: summary),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String value;
  final String label;
  final String? suffix;
  const _StatCard({required this.icon, required this.iconColor, required this.value, required this.label, this.suffix});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Card(
      child: Padding(padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, color: iconColor, size: 28),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(value, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
                if (suffix != null)
                  Padding(padding: const EdgeInsets.only(bottom: 2),
                    child: Text(suffix!, style: TextStyle(color: cs.onSurfaceVariant, fontSize: 12))),
              ],
            ),
            Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: cs.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }
}

class _MotivationCard extends StatelessWidget {
  final WeeklySummary summary;
  const _MotivationCard({required this.summary});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final String msg;
    if (summary.checkinCount >= 7) {
      msg = '完美！本周全勤打卡，坚持就是胜利！';
    } else if (summary.checkinCount >= 5) {
      msg = '很棒！本周打卡 ${summary.checkinCount} 天，继续加油！';
    } else if (summary.checkinCount >= 3) {
      msg = '还不错，但还有提升空间，下周争取每天打卡！';
    } else {
      msg = '本周学习不太稳定，制定一个每日学习计划吧！';
    }
    return Card(
      color: cs.surfaceContainerHighest,
      child: Padding(padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const Text('💡', style: TextStyle(fontSize: 24)),
            const SizedBox(width: 12),
            Expanded(child: Text(msg, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.5))),
          ],
        ),
      ),
    );
  }
}