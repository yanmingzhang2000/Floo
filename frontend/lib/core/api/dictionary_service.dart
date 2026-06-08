import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 查词结果（中文释义）
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
  final String partOfSpeech; // 词性：n. / v. / adj. 等
  final List<DictDefinition> definitions;

  const DictMeaning({
    required this.partOfSpeech,
    required this.definitions,
  });
}

class DictDefinition {
  final String definition; // 中文释义
  final String? example;   // 例句（可能为空）

  const DictDefinition({required this.definition, this.example});
}

/// 调用有道词典非官方接口查词（返回中文释义）
/// 风险：此接口可能随时失效，仅用于快速验证
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

    // 有道词典移动端 API（非官方，可能随时失效）
    final resp = await _dio.get(
      'https://dict.youdao.com/jsonapi',
      queryParameters: {
        'q': key,
        'dicts': '{"count":1,"dicts":[["ec"]]}', // ec = 英汉词典
      },
    );

    final data = resp.data as Map<String, dynamic>;
    
    // 解析返回结构：data['ec']['word'] 包含音标和释义
    final ec = data['ec'] as Map<String, dynamic>?;
    if (ec == null || ec['word'] == null) {
      throw Exception('Word not found');
    }

    final wordData = (ec['word'] as List).first as Map<String, dynamic>;
    
    // 音标：ukphone（英音）或 usphone（美音）
    final phonetic = _extractPhonetic(wordData);

    // 词性 + 释义：trs 数组
    final trs = (wordData['trs'] as List?) ?? [];
    final meanings = <DictMeaning>[];
    
    for (final tr in trs.take(3)) { // 最多取 3 条释义
      final trData = tr as Map<String, dynamic>;
      final trText = (trData['tr'] as List?)?.first['l']['i'] as List?;
      if (trText == null || trText.isEmpty) continue;
      
      final line = trText.first as String; // 格式："n. 人工智能"
      final parts = line.split('. ');
      if (parts.length < 2) {
        // 无词性标注，直接作为释义
        meanings.add(DictMeaning(
          partOfSpeech: '',
          definitions: [DictDefinition(definition: line)],
        ));
        continue;
      }
      
      final pos = parts[0]; // n / v / adj 等
      final def = parts.sublist(1).join('. ');
      meanings.add(DictMeaning(
        partOfSpeech: pos,
        definitions: [DictDefinition(definition: def)],
      ));
    }

    // 如果没有解析到释义，尝试从 basic.explains 获取（简明释义）
    if (meanings.isEmpty) {
      final basic = data['simple']?['word']?.first?['return-phrase'] as Map<String, dynamic>?;
      final explains = basic?['trs'] as List?;
      if (explains != null && explains.isNotEmpty) {
        for (final exp in explains.take(3)) {
          final text = (exp['tr'] as List?)?.first['l']['i']?.first as String?;
          if (text != null) {
            meanings.add(DictMeaning(
              partOfSpeech: '',
              definitions: [DictDefinition(definition: text)],
            ));
          }
        }
      }
    }

    if (meanings.isEmpty) {
      throw Exception('No definitions found');
    }

    final result = DictResult(
      word: word,
      phonetic: phonetic,
      meanings: meanings,
    );

    _cache[key] = result;
    return result;
  }

  String _extractPhonetic(Map<String, dynamic> wordData) {
    // 优先英音，其次美音
    final uk = wordData['ukphone'] as String?;
    if (uk != null && uk.isNotEmpty) return '/$uk/';
    final us = wordData['usphone'] as String?;
    if (us != null && us.isNotEmpty) return '/$us/';
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