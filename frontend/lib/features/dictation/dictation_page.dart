import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/models/content_models.dart';
import '../../core/models/dictation_models.dart';
import '../daily/daily_provider.dart';
import 'dictation_provider.dart';

class DictationPage extends ConsumerStatefulWidget {
  const DictationPage({super.key});

  @override
  ConsumerState<DictationPage> createState() => _DictationPageState();
}

class _DictationPageState extends ConsumerState<DictationPage> {
  final _controller = TextEditingController();
  bool _showOriginal = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final asyncContent = ref.watch(dailyContentProvider);
    final state = ref.watch(dictationControllerProvider);
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('听写练习'),
        actions: [
          IconButton(
            tooltip: _showOriginal ? '隐藏英文原文' : '显示英文原文（参考）',
            icon: Icon(_showOriginal ? Icons.visibility_off_outlined : Icons.visibility_outlined),
            onPressed: () => setState(() => _showOriginal = !_showOriginal),
          ),
          IconButton(
            tooltip: '历史记录',
            icon: const Icon(Icons.history),
            onPressed: () => _showHistorySheet(context),
          ),
        ],
      ),
      body: asyncContent.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _NoContentView(),
        data: (content) => _DictationBody(
          content: content,
          controller: _controller,
          showOriginal: _showOriginal,
          state: state,
          onSubmit: () => _submit(content.id),
          onReset: () {
            _controller.clear();
            ref.read(dictationControllerProvider.notifier).reset();
          },
        ),
      ),
    );
  }

  void _submit(int contentId) {
    if (_controller.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请先输入默写内容')),
      );
      return;
    }
    ref.read(dictationControllerProvider.notifier).submit(
      contentId: contentId,
      userInput: _controller.text,
    );
  }

  void _showHistorySheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => const _HistorySheet(),
    );
  }
}

class _DictationBody extends StatelessWidget {
  final LearningContent content;
  final TextEditingController controller;
  final bool showOriginal;
  final DictationState state;
  final VoidCallback onSubmit;
  final VoidCallback onReset;

  const _DictationBody({
    required this.content,
    required this.controller,
    required this.showOriginal,
    required this.state,
    required this.onSubmit,
    required this.onReset,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // 内容标题提示
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: cs.primaryContainer,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(
            children: [
              Icon(Icons.article_outlined, size: 16, color: cs.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  content.title,
                  style: TextStyle(color: cs.onPrimaryContainer, fontWeight: FontWeight.w600, fontSize: 13),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // 中文翻译提示（默写参考）
        if (content.translation != null && content.translation!.isNotEmpty)
          Card(
            color: cs.secondaryContainer,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.translate, size: 14, color: cs.onSecondaryContainer),
                      const SizedBox(width: 6),
                      Text('中文提示', style: TextStyle(fontSize: 12, color: cs.onSecondaryContainer, fontWeight: FontWeight.w600)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    content.translation!,
                    style: TextStyle(height: 1.7, color: cs.onSecondaryContainer),
                    textAlign: TextAlign.justify,
                  ),
                ],
              ),
            ),
          ),
        const SizedBox(height: 12),

        // 原文（可切换显示，用于对照）
        AnimatedCrossFade(
          duration: const Duration(milliseconds: 250),
          crossFadeState: showOriginal ? CrossFadeState.showFirst : CrossFadeState.showSecond,
          firstChild: Card(
            color: cs.surfaceContainerHighest,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                content.article,
                style: const TextStyle(height: 1.7),
                textAlign: TextAlign.justify,
              ),
            ),
          ),
          secondChild: const SizedBox.shrink(),
        ),
        if (showOriginal) const SizedBox(height: 12),

        // 输入区
        Text('根据中文提示，默写对应英文：', style: Theme.of(context).textTheme.titleSmall?.copyWith(color: cs.onSurfaceVariant)),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          maxLines: 10,
          style: const TextStyle(height: 1.6),
          decoration: InputDecoration(
            hintText: '在这里输入你默写的英文内容...',
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            filled: true,
            fillColor: cs.surfaceContainerLowest,
          ),
        ),
        const SizedBox(height: 12),

        // 操作按钮
        Row(
          children: [
            Expanded(
              child: FilledButton.icon(
                icon: state.loading
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.auto_awesome),
                label: Text(state.loading ? 'AI 批改中...' : '提交批改'),
                onPressed: state.loading ? null : onSubmit,
              ),
            ),
            const SizedBox(width: 8),
            OutlinedButton(
              onPressed: state.loading ? null : onReset,
              child: const Text('清空'),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // 错误提示
        if (state.error != null)
          Card(
            color: cs.errorContainer,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: cs.onErrorContainer),
                  const SizedBox(width: 8),
                  Expanded(child: Text(state.error!, style: TextStyle(color: cs.onErrorContainer))),
                ],
              ),
            ),
          ),

        // 批改结果
        if (state.result != null) _ResultCard(result: state.result!),
      ],
    );
  }
}

class _ResultCard extends StatelessWidget {
  final DictationResult result;
  const _ResultCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final fb = result.feedback;
    final scoreColor = result.score >= 80 ? Colors.green : (result.score >= 60 ? Colors.orange : cs.error);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // 分数卡
        Card(
          color: cs.primaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('本次得分', style: TextStyle(color: cs.onPrimaryContainer, fontSize: 12)),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${result.score}',
                          style: Theme.of(context).textTheme.displaySmall?.copyWith(
                            color: cs.onPrimaryContainer,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.only(bottom: 6, left: 2),
                          child: Text('分', style: TextStyle(color: cs.onPrimaryContainer)),
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('准确率', style: TextStyle(color: cs.onPrimaryContainer, fontSize: 12)),
                    Text('${result.accuracy}%', style: TextStyle(color: cs.onPrimaryContainer, fontWeight: FontWeight.w700, fontSize: 18)),
                  ],
                ),

                const Spacer(),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: cs.tertiaryContainer,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        '+${result.earnedPoints} 积分',
                        style: TextStyle(color: cs.onTertiaryContainer, fontWeight: FontWeight.w600),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '复习阶段 ${result.reviewStage}',
                      style: TextStyle(color: cs.onPrimaryContainer, fontSize: 11),
                    ),
                    if (result.nextReviewAt != null)
                      Text(
                        '下次复习: ${result.nextReviewAt!.month}/${result.nextReviewAt!.day}',
                        style: TextStyle(color: cs.onPrimaryContainer, fontSize: 11),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),

        // AI 评语和差异
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.auto_awesome, size: 18, color: cs.primary),
                    const SizedBox(width: 6),
                    Text('AI 总评', style: Theme.of(context).textTheme.titleMedium),
                  ],
                ),
                const SizedBox(height: 8),
                Text(fb.summary, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.6)),
                if (fb.diffs.isNotEmpty) ...[
                  const Divider(height: 24),
                  Text('差异分析 (${fb.diffs.length}处)', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  ...fb.diffs.map((d) => _DiffRow(diff: d)),
                ],
                if (fb.suggestions.isNotEmpty) ...[
                  const Divider(height: 24),
                  Text('改进建议', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  ...fb.suggestions.map((s) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.tips_and_updates_outlined, size: 14, color: cs.primary),
                        const SizedBox(width: 6),
                        Expanded(child: Text(s, style: Theme.of(context).textTheme.bodySmall)),
                      ],
                    ),
                  )),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _DiffRow extends StatelessWidget {
  final DictationDiff diff;
  const _DiffRow({required this.diff});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final (label, color) = switch (diff.type) {
      'missing' => ('遗漏', cs.errorContainer),
      'wrong'   => ('错误', cs.tertiaryContainer),
      'extra'   => ('多余', cs.secondaryContainer),
      _         => ('差异', cs.surfaceContainerHigh),
    };
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(4)),
            child: Text(label, style: const TextStyle(fontSize: 11)),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text.rich(TextSpan(children: [
              if (diff.expected.isNotEmpty)
                TextSpan(text: '应为「${diff.expected}」', style: const TextStyle(fontWeight: FontWeight.w600)),
              if (diff.actual.isNotEmpty)
                TextSpan(text: '  你写「${diff.actual}」', style: TextStyle(color: cs.error)),
            ])),
          ),
        ],
      ),
    );
  }
}

class _NoContentView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.edit_note, size: 72, color: cs.onSurfaceVariant.withValues(alpha: 0.3)),
            const SizedBox(height: 16),
            const Text('还没有今日内容', style: TextStyle(fontSize: 16)),
            const SizedBox(height: 8),
            Text('请先前往「每日学习」生成今日文章', style: TextStyle(color: cs.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }
}

class _HistorySheet extends ConsumerWidget {
  const _HistorySheet();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncHistory = ref.watch(dictationHistoryProvider);
    final cs = Theme.of(context).colorScheme;
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.6,
      maxChildSize: 0.9,
      builder: (_, scrollController) => Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Text('听写历史', style: Theme.of(context).textTheme.titleLarge),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),
          const Divider(height: 0),
          Expanded(
            child: asyncHistory.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('加载失败: $e')),
              data: (list) => list.isEmpty
                  ? const Center(child: Text('暂无记录'))
                  : ListView.separated(
                      controller: scrollController,
                      padding: const EdgeInsets.all(16),
                      itemCount: list.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (_, i) => _HistoryTile(item: list[i]),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _HistoryTile extends StatelessWidget {
  final DictationHistory item;
  const _HistoryTile({required this.item});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final scoreColor = item.score >= 80
        ? Colors.green.shade700
        : (item.score >= 60 ? Colors.orange.shade700 : cs.error);
    final d = item.createdAt;
    final dateStr = '${d.month}/${d.day} ${d.hour.toString().padLeft(2,'0')}:${d.minute.toString().padLeft(2,'0')}';
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: cs.primaryContainer,
          child: Text('${item.score}', style: TextStyle(color: scoreColor, fontWeight: FontWeight.w800, fontSize: 13)),
        ),
        title: Text('第 ${item.dictationId} 次默写', maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text('准确率 ${item.accuracyRate.toStringAsFixed(0)}%  · $dateStr'),
        trailing: Text('+${item.earnedPoints}分', style: TextStyle(color: cs.primary, fontWeight: FontWeight.w600)),
      ),
    );
  }
}