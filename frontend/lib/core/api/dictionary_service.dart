import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';

/// Free Dictionary API 查词结果
class DictResult {
  final String word;
  final String phonetic;
  final List<DictMeaning> meanings;

  const DictResult({
    required this.word,
    required this.phonetic,
    required this.meanings,
  });
}

class DictMeaning {
  final String partOfSpeech;
  final List<DictDefinition> definitions;

  const DictMeaning({
    required this.partOfSpeech,
    required this.definitions,
  });
}

class DictDefinition {
  final String definition;
  final String? example;

  const DictDefinition({required this.definition, this.example});
}

/// 调用 https://api.dictionaryapi.dev 查词
/// 上游保证 word 非空，不再校验
class DictionaryService {
  final Dio _dio;

  // 简单内存缓存，避免同一个词重复请求
  final Map<String, DictResult> _cache = {};

  DictionaryService(this._dio);

  Future<DictResult> lookup(String word) async {
    final key = word.toLowerCase();
    if (_cache.containsKey(key)) {
      return _cache[key]!;
    }

    final resp = await _dio.get(
      'https://api.dictionaryapi.dev/api/v2/entries/en/$key',
    );

    final data = resp.data as List;
    final entry = data.first as Map<String, dynamic>;

    // 取第一个音标（部分词条音标在 phonetics 数组里）
    final phonetic = (entry['phonetic'] as String?) ??
        _extractPhonetic(entry['phonetics'] as List? ?? []);

    final meanings = ((entry['meanings'] as List?) ?? [])
        .take(2) // 最多展示 2 种词性
        .map((m) {
      final defs = ((m['definitions'] as List?) ?? [])
          .take(2) // 每种词性最多展示 2 条释义
          .map((d) => DictDefinition(
                definition: d['definition'] as String? ?? '',
                example: d['example'] as String?,
              ))
          .toList();
      return DictMeaning(
        partOfSpeech: m['partOfSpeech'] as String? ?? '',
        definitions: defs,
      );
    }).toList();

    final result = DictResult(
      word: entry['word'] as String? ?? word,
      phonetic: phonetic,
      meanings: meanings,
    );

    _cache[key] = result;
    return result;
  }

  String _extractPhonetic(List phonetics) {
    for (final p in phonetics) {
      final text = (p as Map<String, dynamic>)['text'] as String?;
      if (text != null && text.isNotEmpty) return text;
    }
    return '';
  }
}

final dictionaryServiceProvider = Provider<DictionaryService>((ref) {
  // 用独立的 Dio 实例，baseUrl 指向外部词典 API，不走后端
  final dio = Dio(BaseOptions(
    connectTimeout: const Duration(seconds: 8),
    receiveTimeout: const Duration(seconds: 10),
  ));
  return DictionaryService(dio);
});