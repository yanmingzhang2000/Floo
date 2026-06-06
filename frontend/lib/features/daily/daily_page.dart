import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/models/content_models.dart';
import 'daily_provider.dart';

class DailyPage extends ConsumerWidget {
  const DailyPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncContent = ref.watch(dailyContentProvider);
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: asyncContent.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorView(
          message: _friendlyError(e),
          onGenerate: () => _generateNew(context, ref),
        ),
        data: (content) => _DailyBody(content: content),
      ),
    );
  }

  Future<void> _generateNew(BuildContext context, WidgetRef ref) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.refresh(generateDailyProvider.future);
      ref.invalidate(dailyContentProvider);
      messenger.showSnackBar(const SnackBar(content: Text('新内容已生成')));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('生成失败: $e')));
    }
  }

  String _friendlyError(Object e) {
    final s = e.toString();
    if (s.contains('404')) return '今日还没有学习内容，点击下方生成';
    if (s.contains('connection') || s.contains('SocketException')) return '网络连接失败，请检查网络';
    return '加载失败，请重试';
  }
}

class _DailyBody extends ConsumerWidget {
  final LearningContent content;
  const _DailyBody({required this.content});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 160,
          pinned: true,
          backgroundColor: cs.primaryContainer,
          flexibleSpace: FlexibleSpaceBar(
            title: Text(
              content.title,
              style: TextStyle(
                color: cs.onPrimaryContainer,
                fontWeight: FontWeight.w700,
                fontSize: 14,
              ),
            ),
            background: Stack(
              fit: StackFit.expand,
              children: [
                Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [cs.primary, cs.primaryContainer],
                    ),
                  ),
                ),
                Positioned(
                  right: -20,
                  top: -20,
                  child: Icon(
                    Icons.auto_stories_outlined,
                    size: 160,
                    color: cs.onPrimary.withValues(alpha: 0.08),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            IconButton(
              tooltip: '生成新内容',
              icon: const Icon(Icons.auto_awesome_outlined),
              color: Colors.white,
              onPressed: () => _generateNew(context, ref),
            ),
            IconButton(
              tooltip: '历史内容',
              icon: const Icon(Icons.history),
              color: Colors.white,
              onPressed: () => context.push('/daily/list'),
            ),
          ],
        ),
        SliverPadding(
          padding: const EdgeInsets.all(16),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _MetaRow(content: content),
              const SizedBox(height: 16),
              _ArticleCard(content: content),
              const SizedBox(height: 12),
              if (content.translation != null && content.translation!.isNotEmpty)
                _TranslationCard(translation: content.translation!),
              const SizedBox(height: 24),
              if (content.keyWords.isNotEmpty) ...[
                Row(
                  children: [
                    Icon(Icons.local_fire_department, color: cs.primary, size: 20),
                    const SizedBox(width: 6),
                    Text('核心词汇', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                    const Spacer(),
                    Text('${content.keyWords.length} 个词', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: cs.onSurfaceVariant)),
                  ],
                ),
                const SizedBox(height: 8),
                _KeyWordsWrap(words: content.keyWords),
                const SizedBox(height: 24),
              ],
              FilledButton.icon(
                icon: const Icon(Icons.edit_note),
                label: const Text('开始默写练习'),
                onPressed: () => context.go('/dictation'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                icon: const Icon(Icons.replay_outlined),
                label: const Text('查看复习任务'),
                onPressed: () => context.go('/review'),
              ),
              const SizedBox(height: 24),
            ]),
          ),
        ),
      ],
    );
  }

  Future<void> _generateNew(BuildContext context, WidgetRef ref) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.refresh(generateDailyProvider.future);
      ref.invalidate(dailyContentProvider);
      messenger.showSnackBar(const SnackBar(content: Text('新内容已生成')));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('生成失败: $e')));
    }
  }
}

class _MetaRow extends StatelessWidget {
  final LearningContent content;
  const _MetaRow({required this.content});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final diffLabel = {'easy': '初级', 'medium': '中级', 'hard': '高级'}[content.difficultyLevel] ?? content.difficultyLevel;
    final themeLabel = {
      'tech': '科技', 'business': '商业', 'culture': '文化', 'daily': '日常', 'mixed': '综合'
    }[content.themeType] ?? content.themeType;
    final d = content.contentDate;
    final dateStr = '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    return Wrap(
      spacing: 8,
      runSpacing: 6,
      children: [
        _Chip(label: dateStr, icon: Icons.calendar_today_outlined, color: cs.secondaryContainer, textColor: cs.onSecondaryContainer),
        _Chip(label: diffLabel, icon: Icons.bar_chart, color: cs.tertiaryContainer, textColor: cs.onTertiaryContainer),
        _Chip(label: themeLabel, icon: Icons.category_outlined, color: cs.primaryContainer, textColor: cs.onPrimaryContainer),
      ],
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final Color textColor;
  const _Chip({required this.label, required this.icon, required this.color, required this.textColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(20)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: textColor),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(fontSize: 12, color: textColor, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}

class _ArticleCard extends StatelessWidget {
  final LearningContent content;
  const _ArticleCard({required this.content});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final keyWordSet = content.keyWords.map((w) => w.toLowerCase()).toSet();
    final spans = <TextSpan>[];
    final regex = RegExp(r"[A-Za-z']+|[^A-Za-z']+");
    for (final m in regex.allMatches(content.article)) {
      final token = m.group(0)!;
      final isKey = keyWordSet.contains(token.toLowerCase());
      spans.add(TextSpan(
        text: token,
        style: isKey
            ? TextStyle(
                color: cs.primary,
                fontWeight: FontWeight.w700,
                backgroundColor: cs.primaryContainer.withValues(alpha: 0.5),
              )
            : null,
      ));
    }
    return Card(
      color: cs.surfaceContainerHighest,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: RichText(
          text: TextSpan(
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.8),
            children: spans,
          ),
        ),
      ),
    );
  }
}

class _TranslationCard extends StatefulWidget {
  final String translation;
  const _TranslationCard({required this.translation});

  @override
  State<_TranslationCard> createState() => _TranslationCardState();
}

class _TranslationCardState extends State<_TranslationCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => setState(() => _expanded = !_expanded),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.translate, size: 18, color: cs.primary),
                  const SizedBox(width: 8),
                  Text('中文译文', style: Theme.of(context).textTheme.titleSmall),
                  const Spacer(),
                  Icon(_expanded ? Icons.expand_less : Icons.expand_more, color: cs.onSurfaceVariant),
                ],
              ),
              if (_expanded) ...[
                const SizedBox(height: 12),
                Text(widget.translation, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.6, color: cs.onSurfaceVariant)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _KeyWordsWrap extends StatelessWidget {
  final List<String> words;
  const _KeyWordsWrap({required this.words});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: words.map((w) => Chip(
        avatar: Icon(Icons.local_fire_department, size: 14, color: cs.primary),
        label: Text(w, style: const TextStyle(fontWeight: FontWeight.w600)),
        backgroundColor: cs.primaryContainer,
        labelStyle: TextStyle(color: cs.onPrimaryContainer),
        padding: EdgeInsets.zero,
        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      )).toList(),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onGenerate;
  const _ErrorView({required this.message, required this.onGenerate});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.article_outlined, size: 80, color: cs.onSurfaceVariant.withValues(alpha: 0.4)),
            const SizedBox(height: 16),
            Text(message, style: Theme.of(context).textTheme.bodyLarge, textAlign: TextAlign.center),
            const SizedBox(height: 24),
            FilledButton.icon(
              icon: const Icon(Icons.auto_awesome),
              label: const Text('AI 生成今日内容'),
              onPressed: onGenerate,
            ),
          ],
        ),
      ),
    );
  }
}