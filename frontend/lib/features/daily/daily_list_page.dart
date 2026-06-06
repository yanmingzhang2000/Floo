import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/models/content_models.dart';
import 'daily_provider.dart';

class DailyListPage extends ConsumerWidget {
  const DailyListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncList = ref.watch(dailyListProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('历史内容')),
      body: asyncList.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('加载失败: $e')),
        data: (list) => list.isEmpty
            ? const Center(child: Text('暂无历史内容'))
            : ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: list.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, i) => _ContentTile(item: list[i]),
              ),
      ),
    );
  }
}

class _ContentTile extends StatelessWidget {
  final LearningContent item;
  const _ContentTile({required this.item});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final d = item.contentDate;
    final dateStr = '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    final diffLabel = {'easy': '初级', 'medium': '中级', 'hard': '高级'}[item.difficultyLevel] ?? item.difficultyLevel;

    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(
          backgroundColor: cs.primaryContainer,
          child: Icon(Icons.article_outlined, color: cs.primary, size: 20),
        ),
        title: Text(item.title, style: const TextStyle(fontWeight: FontWeight.w600), maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Row(
          children: [
            Text(dateStr, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(color: cs.tertiaryContainer, borderRadius: BorderRadius.circular(4)),
              child: Text(diffLabel, style: TextStyle(fontSize: 10, color: cs.onTertiaryContainer)),
            ),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push('/daily/content/${item.id}'),
      ),
    );
  }
}