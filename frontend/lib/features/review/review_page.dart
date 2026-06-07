import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/models/content_models.dart';
import '../daily/daily_provider.dart';

class ReviewPage extends ConsumerWidget {
  const ReviewPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncTasks = ref.watch(reviewListProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('复习任务'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(reviewListProvider),
          ),
        ],
      ),
      body: asyncTasks.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('加载失败: $e')),
        data: (tasks) => tasks.isEmpty
            ? _EmptyView()
            : _TaskList(tasks: tasks),
      ),
    );
  }
}

class _TaskList extends StatelessWidget {
  final List<ReviewTask> tasks;
  const _TaskList({required this.tasks});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Column(
      children: [
        // 顶部统计
        Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: cs.secondaryContainer.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              Icon(Icons.pending_actions, color: cs.primary),
              const SizedBox(width: 8),
              Text('今日待复习', style: TextStyle(color: cs.onPrimaryContainer)),
              const Spacer(),
              Text('${tasks.length} 篇',
                  style: TextStyle(
                      color: cs.onPrimaryContainer,
                      fontWeight: FontWeight.w800,
                      fontSize: 18)),
            ],
          ),
        ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: tasks.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, i) => _ReviewTaskTile(task: tasks[i]),
          ),
        ),
      ],
    );
  }
}

class _ReviewTaskTile extends StatelessWidget {
  final ReviewTask task;
  const _ReviewTaskTile({required this.task});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final stageColor = task.reviewStage >= 5
        ? cs.tertiaryContainer
        : (task.reviewStage >= 3 ? cs.secondaryContainer : cs.primaryContainer);
    final accuracyStr = task.lastAccuracy > 0
        ? '上次准确率 ${task.lastAccuracy.toStringAsFixed(0)}%'
        : '应复习时间: ${_formatDate(task.nextReviewAt)}';

    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(
          backgroundColor: stageColor,
          child: Text(
            'S${task.reviewStage}',
            style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12, color: cs.onSurface),
          ),
        ),
        title: Text(task.title,
            style: const TextStyle(fontWeight: FontWeight.w600),
            maxLines: 1,
            overflow: TextOverflow.ellipsis),
        subtitle: Text(accuracyStr),
        trailing: FilledButton.tonal(
          onPressed: () => context.push('/daily/content/${task.contentId}'),
          child: const Text('去复习'),
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.month}/${dt.day} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }
}

class _EmptyView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.done_all, size: 80, color: Colors.green.shade400),
          const SizedBox(height: 16),
          const Text('今日无待复习内容', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text('保持学习，明天继续！', style: TextStyle(color: cs.onSurfaceVariant)),
        ],
      ),
    );
  }
}