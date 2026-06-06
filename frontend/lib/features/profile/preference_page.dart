import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/models/user_models.dart';
import '../../core/providers/auth_provider.dart';

class PreferencePage extends ConsumerStatefulWidget {
  const PreferencePage({super.key});

  @override
  ConsumerState<PreferencePage> createState() => _PreferencePageState();
}

class _PreferencePageState extends ConsumerState<PreferencePage> {
  String _difficulty = 'medium';
  String _theme = 'mixed';
  int _dailyGoal = 15;
  bool _saving = false;
  bool _loaded = false;

  @override
  void initState() {
    super.initState();
    // 加载当前偏好
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadPref());
  }

  Future<void> _loadPref() async {
    try {
      final pref = await ref.read(userPreferenceProvider.future);
      if (mounted) {
        setState(() {
          _difficulty = pref.difficultyLevel;
          _theme = pref.themeType;
          _dailyGoal = pref.dailyGoalMinutes;
          _loaded = true;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loaded = true);
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final dio = ref.read(dioProvider);
      final userId = ref.read(currentUserIdProvider);
      await dio.put('/api/user/$userId/preference', data: {
        'difficulty_level': _difficulty,
        'theme_type': _theme,
        'daily_goal_minutes': _dailyGoal,
      });
      ref.invalidate(userPreferenceProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('偏好设置已保存')));
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('保存失败: $e')));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('学习偏好设置'),
        actions: [
          TextButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('保存'),
          ),
        ],
      ),
      body: !_loaded
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // 难度选择
                Text('文章难度', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                _SegmentRow(
                  options: const [('easy', '初级'), ('medium', '中级'), ('hard', '高级')],
                  selected: _difficulty,
                  onChanged: (v) => setState(() => _difficulty = v),
                ),
                const SizedBox(height: 24),

                // 主题选择
                Text('内容主题', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final (val, label, icon) in [
                      ('tech', '科技', Icons.computer),
                      ('business', '商业', Icons.business_center),
                      ('culture', '文化', Icons.museum),
                      ('daily', '日常', Icons.home),
                      ('mixed', '综合', Icons.shuffle),
                    ])
                      FilterChip(
                        avatar: Icon(icon, size: 16),
                        label: Text(label),
                        selected: _theme == val,
                        onSelected: (_) => setState(() => _theme = val),
                        selectedColor: cs.primaryContainer,
                      ),
                  ],
                ),
                const SizedBox(height: 24),

                // 每日目标
                Text('每日学习目标', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                Text('$_dailyGoal 分钟', style: TextStyle(color: cs.primary, fontWeight: FontWeight.w600, fontSize: 18)),
                Slider(
                  value: _dailyGoal.toDouble(),
                  min: 5,
                  max: 60,
                  divisions: 11,
                  label: '$_dailyGoal 分钟',
                  onChanged: (v) => setState(() => _dailyGoal = v.round()),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('5分钟', style: TextStyle(color: cs.onSurfaceVariant, fontSize: 11)),
                    Text('60分钟', style: TextStyle(color: cs.onSurfaceVariant, fontSize: 11)),
                  ],
                ),
              ],
            ),
    );
  }
}

class _SegmentRow extends StatelessWidget {
  final List<(String, String)> options;
  final String selected;
  final ValueChanged<String> onChanged;
  const _SegmentRow({required this.options, required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Row(
      children: options.map((opt) {
        final (val, label) = opt;
        final isSelected = selected == val;
        return Expanded(
          child: GestureDetector(
            onTap: () => onChanged(val),
            child: Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(vertical: 12),
              decoration: BoxDecoration(
                color: isSelected ? cs.primary : cs.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(10),
              ),
              alignment: Alignment.center,
              child: Text(label,
                  style: TextStyle(
                      color: isSelected ? cs.onPrimary : cs.onSurface,
                      fontWeight: FontWeight.w600)),
            ),
          ),
        );
      }).toList(),
    );
  }
}