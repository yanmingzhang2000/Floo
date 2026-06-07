import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api/api_client.dart';
import '../../core/models/content_models.dart';

// 按 content_id 拉取单篇内容的 provider
final contentDetailProvider =
    FutureProvider.autoDispose.family<LearningContent, int>((ref, contentId) async {
  final dio = ref.watch(dioProvider);
  final resp = await dio.get('/api/daily/content/$contentId');
  return LearningContent.fromJson(resp.data as Map<String, dynamic>);
});

class DailyContentDetailPage extends ConsumerWidget {
  final int contentId;
  const DailyContentDetailPage({super.key, required this.contentId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncContent = ref.watch(contentDetailProvider(contentId));
    return asyncContent.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (e, _) => Scaffold(
        appBar: AppBar(),
        body: Center(child: Text('加载失败: $e')),
      ),
      data: (content) => _DetailScaffold(content: content),
    );
  }
}

class _DetailScaffold extends StatelessWidget {
  final LearningContent content;
  const _DetailScaffold({required this.content});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 140,
            pinned: true,
            backgroundColor: cs.primaryContainer,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                content.title,
                style: TextStyle(color: cs.onPrimaryContainer, fontWeight: FontWeight.w700, fontSize: 13),
              ),
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
            actions: [
              IconButton(
                icon: const Icon(Icons.edit_note, color: Colors.white),
                tooltip: '去默写',
                onPressed: () => context.go('/dictation'),
              ),
            ],
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // 元信息
                _MetaChips(content: content),
                const SizedBox(height: 16),
                // 正文
                Card(
                  color: cs.surfaceContainerHighest,
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: _HighlightedText(content: content),
                  ),
                ),
                // 译文
                if (content.translation != null && content.translation!.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.translate, size: 16, color: cs.primary),
                              const SizedBox(width: 6),
                              Text('中文译文', style: Theme.of(context).textTheme.titleSmall),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(content.translation!,
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  height: 1.6, color: cs.onSurfaceVariant),
                              textAlign: TextAlign.justify),
                        ],
                      ),
                    ),
                  ),
                ],
                // 词汇
                if (content.words.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Text('核心词汇', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8, runSpacing: 8,
                    children: content.words.map((w) => Chip(
                      label: Text(w.word, style: const TextStyle(fontWeight: FontWeight.w600)),
                      backgroundColor: cs.primaryContainer,
                      labelStyle: TextStyle(color: cs.onPrimaryContainer),
                    )).toList(),
                  ),
                ],
                const SizedBox(height: 32),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

class _MetaChips extends StatelessWidget {
  final LearningContent content;
  const _MetaChips({required this.content});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final diffLabel = {'easy': '初级', 'medium': '中级', 'hard': '高级'}[content.difficultyLevel] ?? content.difficultyLevel;
    final themeLabel = {
      'ai_tech': 'AI科技', 'product_tech': '产品技术', 'business': '财经商业',
      'daily_news': '日常新闻', 'self_growth': '个人成长', 'all_random': '随机',
    }[content.themeType] ?? content.themeType;
    final d = content.contentDate;
    final dateStr = '${d.year}-${d.month.toString().padLeft(2,'0')}-${d.day.toString().padLeft(2,'0')}';
    return Wrap(spacing: 8, runSpacing: 6, children: [
      _chip(dateStr, cs.secondaryContainer, cs.onSecondaryContainer),
      _chip(diffLabel, cs.tertiaryContainer, cs.onTertiaryContainer),
      _chip(themeLabel, cs.primaryContainer, cs.onPrimaryContainer),
    ]);
  }

  Widget _chip(String label, Color bg, Color fg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(20)),
      child: Text(label, style: TextStyle(fontSize: 12, color: fg, fontWeight: FontWeight.w500)),
    );
  }
}

class _HighlightedText extends StatelessWidget {
  final LearningContent content;
  const _HighlightedText({required this.content});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final keySet = content.keyWordStrings.toSet();
    final spans = <TextSpan>[];
    final regex = RegExp(r"[A-Za-z']+|[^A-Za-z']+");
    for (final m in regex.allMatches(content.article)) {
      final token = m.group(0)!;
      final isKey = keySet.contains(token.toLowerCase());
      spans.add(TextSpan(
        text: token,
        style: isKey
            ? TextStyle(color: cs.primary, fontWeight: FontWeight.w700,
                backgroundColor: cs.primaryContainer.withValues(alpha: 0.5))
            : null,
      ));
    }
    return RichText(
      textAlign: TextAlign.justify,
      text: TextSpan(
        style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.8),
        children: spans,
      ),
    );
  }
}
