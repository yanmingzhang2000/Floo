import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/models/content_models.dart';
import 'daily_provider.dart';

class DailyPage extends ConsumerWidget {
  const DailyPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncList = ref.watch(todayListProvider);
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: asyncList.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorView(
          message: _friendlyError(e),
          onGenerate: () => _generateNew(context, ref),
        ),
        data: (list) => list.contents.isEmpty
            ? _ErrorView(
                message: '今日还没有学习内容，点击下方生成',
                onGenerate: () => _generateNew(context, ref),
              )
            : _DailyListBody(todayList: list),
      ),
    );
  }

  Future<void> _generateNew(BuildContext context, WidgetRef ref) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.refresh(generateDailyProvider.future);
      ref.invalidate(todayListProvider);
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

class _DailyListBody extends ConsumerWidget {
  final TodayContentList todayList;
  const _DailyListBody({required this.todayList});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    final visible = todayList.visibleContents;
    final themeLabel = {
      'ai_tech': 'AI科技',
      'product_tech': '产品技术',
      'business': '财经商业',
      'daily_news': '日常新闻',
      'self_growth': '个人成长',
      'all_random': '随机',
    }[todayList.theme] ?? todayList.theme;

    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 140,
          pinned: true,
          backgroundColor: cs.primary,
          flexibleSpace: FlexibleSpaceBar(
            title: Text(
              '今日英语 · $themeLabel',
              style: const TextStyle(
                  color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
            ),
            background: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [cs.primary, cs.primaryContainer],
                ),
              ),
              child: Align(
                alignment: Alignment.centerRight,
                child: Padding(
                  padding: const EdgeInsets.only(right: 16),
                  child: Icon(Icons.auto_stories_outlined,
                      size: 120, color: Colors.white.withValues(alpha: 0.08)),
                ),
              ),
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
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _GoalBanner(todayList: todayList),
              const SizedBox(height: 16),
              ...visible.asMap().entries.map((entry) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: _ContentCard(content: entry.value, index: entry.key),
                );
              }),
              const SizedBox(height: 8),
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
      ref.invalidate(todayListProvider);
      messenger.showSnackBar(const SnackBar(content: Text('新内容已生成')));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text('生成失败: $e')));
    }
  }
}

class _GoalBanner extends StatelessWidget {
  final TodayContentList todayList;
  const _GoalBanner({required this.todayList});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final goal = todayList.dailyGoalMinutes;
    final count = todayList.visibleContents.length;
    final total = todayList.contents.length;
    final hint = count >= total
        ? '今日全部 $total 篇内容'
        : '根据 $goal 分钟目标，为你展示 $count/$total 篇';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: cs.secondaryContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(Icons.timer_outlined, size: 16, color: cs.onSecondaryContainer),
          const SizedBox(width: 8),
          Text(hint,
              style: TextStyle(
                  fontSize: 13,
                  color: cs.onSecondaryContainer,
                  fontWeight: FontWeight.w500)),
          const Spacer(),
          Text('$goal 分钟',
              style: TextStyle(
                  fontSize: 13,
                  color: cs.secondary,
                  fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _ContentCard extends StatelessWidget {
  final LearningContent content;
  final int index;
  const _ContentCard({required this.content, required this.index});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final isOverview = content.isOverview;

    return Card(
      elevation: isOverview ? 3 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: isOverview
            ? BorderSide(color: cs.primary.withValues(alpha: 0.4), width: 1.5)
            : BorderSide.none,
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: isOverview ? cs.primary : cs.secondaryContainer,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    isOverview ? '今日总览' : '文章 $index',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: isOverview ? cs.onPrimary : cs.onSecondaryContainer,
                    ),
                  ),
                ),
                const Spacer(),
                if (content.audioUrl != null)
                  GestureDetector(
                    onTap: () {},
                    child: Icon(Icons.open_in_new,
                        size: 16, color: cs.onSurfaceVariant),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            Text(content.title,
                style: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700, height: 1.3)),
            const SizedBox(height: 12),
            _ArticleText(content: content),
            if (content.translation != null &&
                content.translation!.isNotEmpty) ...[
              const SizedBox(height: 12),
              _TranslationCard(translation: content.translation!),
            ],
            if (content.words.isNotEmpty) ...[
              const SizedBox(height: 12),
              _WordsSection(words: content.words),
            ],
          ],
        ),
      ),
    );
  }
}

class _ArticleText extends StatefulWidget {
  final LearningContent content;
  const _ArticleText({required this.content});

  @override
  State<_ArticleText> createState() => _ArticleTextState();
}

class _ArticleTextState extends State<_ArticleText> {
  OverlayEntry? _overlay;

  // 构建单词对应的 WordItem 查找表（小写 key）
  Map<String, WordItem> get _wordMap => {
        for (final w in widget.content.words) w.word.toLowerCase(): w,
      };

  void _showPopover(BuildContext context, String word, Offset globalOffset) {
    _dismissPopover();
    final wordItem = _wordMap[word.toLowerCase()];
    final overlay = Overlay.of(context);
    _overlay = OverlayEntry(
      builder: (_) => _WordPopover(
        word: word,
        wordItem: wordItem,
        anchor: globalOffset,
        onDismiss: _dismissPopover,
      ),
    );
    overlay.insert(_overlay!);
  }

  void _dismissPopover() {
    _overlay?.remove();
    _overlay = null;
  }

  @override
  void dispose() {
    _dismissPopover();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final keyWordSet = widget.content.keyWordStrings.toSet();
    final baseStyle =
        Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.8);
    final spans = <InlineSpan>[];
    final regex = RegExp(r"[A-Za-z']+|[^A-Za-z']+");

    for (final m in regex.allMatches(widget.content.article)) {
      final token = m.group(0)!;
      // 非英语 token（标点、空格等）直接渲染文本
      if (!RegExp(r"[A-Za-z]").hasMatch(token)) {
        spans.add(TextSpan(text: token));
        continue;
      }
      final isKey = keyWordSet.contains(token.toLowerCase());
      // 每个英语单词用 WidgetSpan 包裹，支持点击
      spans.add(WidgetSpan(
        alignment: PlaceholderAlignment.baseline,
        baseline: TextBaseline.alphabetic,
        child: GestureDetector(
          onTapUp: (details) =>
              _showPopover(context, token, details.globalPosition),
          child: Text(
            token,
            style: baseStyle?.copyWith(
              color: isKey ? cs.primary : cs.onSurface,
              fontWeight: isKey ? FontWeight.w700 : FontWeight.normal,
              // 核心词加下划线虚线，暗示可点击
              decoration: isKey ? TextDecoration.underline : null,
              decorationStyle: TextDecorationStyle.dotted,
              decorationColor: cs.primary.withValues(alpha: 0.5),
            ),
          ),
        ),
      ));
    }

    return RichText(
      textAlign: TextAlign.justify,
      text: TextSpan(style: baseStyle, children: spans),
    );
  }
}

/// 单词悬浮卡片
class _WordPopover extends StatelessWidget {
  final String word;
  final WordItem? wordItem;
  final Offset anchor;
  final VoidCallback onDismiss;

  const _WordPopover({
    required this.word,
    required this.wordItem,
    required this.anchor,
    required this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final screenSize = MediaQuery.of(context).size;
    const cardWidth = 240.0;
    const cardMaxHeight = 180.0;
    const margin = 12.0;

    // 计算卡片左边缘，避免超出屏幕右侧
    double left = anchor.dx - cardWidth / 2;
    left = left.clamp(margin, screenSize.width - cardWidth - margin);

    // 默认显示在点击点上方，如果上方空间不足则显示在下方
    double top = anchor.dy - cardMaxHeight - 8;
    if (top < margin) top = anchor.dy + 24;

    return Stack(
      children: [
        // 透明遮罩层，点击任意处关闭
        Positioned.fill(
          child: GestureDetector(
            onTap: onDismiss,
            behavior: HitTestBehavior.translucent,
          ),
        ),
        // 卡片本体
        Positioned(
          left: left,
          top: top,
          width: cardWidth,
          child: Material(
            elevation: 8,
            borderRadius: BorderRadius.circular(14),
            shadowColor: cs.primary.withValues(alpha: 0.25),
            child: Container(
              decoration: BoxDecoration(
                color: cs.surface,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                    color: cs.primary.withValues(alpha: 0.2), width: 1),
              ),
              padding: const EdgeInsets.all(14),
              child: wordItem != null
                  ? _KnownWordContent(wordItem: wordItem!, cs: cs)
                  : _UnknownWordContent(word: word, cs: cs),
            ),
          ),
        ),
      ],
    );
  }
}

/// 已收录词汇的卡片内容
class _KnownWordContent extends StatelessWidget {
  final WordItem wordItem;
  final ColorScheme cs;
  const _KnownWordContent({required this.wordItem, required this.cs});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // 单词 + 音标行
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            Expanded(
              child: Text(
                wordItem.word,
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: cs.primary),
              ),
            ),
            if (wordItem.phonetic.isNotEmpty)
              Text(
                wordItem.phonetic,
                style: TextStyle(fontSize: 11, color: cs.onSurfaceVariant),
              ),
          ],
        ),
        if (wordItem.meaning.isNotEmpty) ...
          [
            const SizedBox(height: 6),
            Text(
              wordItem.meaning,
              style: TextStyle(
                  fontSize: 13,
                  color: cs.onSurface,
                  fontWeight: FontWeight.w600),
            ),
          ],
        if (wordItem.usage.isNotEmpty) ...
          [
            const SizedBox(height: 8),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
              decoration: BoxDecoration(
                color: cs.primaryContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                wordItem.usage,
                style: TextStyle(
                    fontSize: 12,
                    color: cs.onPrimaryContainer,
                    height: 1.5,
                    fontStyle: FontStyle.italic),
              ),
            ),
          ],
      ],
    );
  }
}

/// 未收录词汇的卡片内容
class _UnknownWordContent extends StatelessWidget {
  final String word;
  final ColorScheme cs;
  const _UnknownWordContent({required this.word, required this.cs});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          word,
          style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: cs.onSurface),
        ),
        const SizedBox(height: 6),
        Text(
          '非本篇核心词汇',
          style: TextStyle(fontSize: 12, color: cs.onSurfaceVariant),
        ),
      ],
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
      color: cs.surfaceContainerHighest,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => setState(() => _expanded = !_expanded),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.translate, size: 16, color: cs.primary),
                  const SizedBox(width: 6),
                  Text('中文译文',
                      style: Theme.of(context)
                          .textTheme
                          .titleSmall
                          ?.copyWith(fontSize: 13)),
                  const Spacer(),
                  Icon(
                      _expanded ? Icons.expand_less : Icons.expand_more,
                      color: cs.onSurfaceVariant,
                      size: 18),
                ],
              ),
              if (_expanded) ...[
                const SizedBox(height: 10),
                Text(widget.translation,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        height: 1.6, color: cs.onSurfaceVariant),
                    textAlign: TextAlign.justify),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _WordsSection extends StatelessWidget {
  final List<WordItem> words;
  const _WordsSection({required this.words});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.local_fire_department, color: cs.primary, size: 16),
            const SizedBox(width: 4),
            Text('核心词汇',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    fontWeight: FontWeight.w700, color: cs.primary)),
            const SizedBox(width: 6),
            Text('${words.length} 个',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: cs.onSurfaceVariant)),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: words.map((w) => _WordChip(word: w)).toList(),
        ),
      ],
    );
  }
}

class _WordChip extends StatelessWidget {
  final WordItem word;
  const _WordChip({required this.word});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: cs.secondaryContainer.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(word.word,
              style: TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                  color: cs.onSurface)),
          if (word.phonetic.isNotEmpty)
            Text(word.phonetic,
                style: TextStyle(fontSize: 10, color: cs.onSurfaceVariant)),
          if (word.meaning.isNotEmpty)
            Text(word.meaning,
                style: TextStyle(
                    fontSize: 11,
                    color: cs.primary,
                    fontWeight: FontWeight.w500)),
        ],
      ),
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
            Icon(Icons.article_outlined,
                size: 80,
                color: cs.onSurfaceVariant.withValues(alpha: 0.4)),
            const SizedBox(height: 16),
            Text(message,
                style: Theme.of(context).textTheme.bodyLarge,
                textAlign: TextAlign.center),
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