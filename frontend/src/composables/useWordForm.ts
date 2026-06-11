/**
 * 词形还原工具
 * 将单词的各种变形还原为原型
 */

// 常见不规则动词映射
const IRREGULAR_VERBS: Record<string, string> = {
  'went': 'go', 'gone': 'go', 'going': 'go', 'goes': 'go',
  'came': 'come', 'coming': 'come', 'comes': 'come',
  'took': 'take', 'taken': 'take', 'taking': 'take', 'takes': 'take',
  'made': 'make', 'making': 'make', 'makes': 'make',
  'said': 'say', 'saying': 'say', 'says': 'say',
  'got': 'get', 'gotten': 'get', 'getting': 'get', 'gets': 'get',
  'gave': 'give', 'given': 'give', 'giving': 'give', 'gives': 'give',
  'found': 'find', 'finding': 'find', 'finds': 'find',
  'knew': 'know', 'known': 'know', 'knowing': 'know', 'knows': 'know',
  'thought': 'think', 'thinking': 'think', 'thinks': 'think',
  'saw': 'see', 'seen': 'see', 'seeing': 'see', 'sees': 'see',
  'left': 'leave', 'leaving': 'leave', 'leaves': 'leave',
  'began': 'begin', 'begun': 'begin', 'beginning': 'begin', 'begins': 'begin',
  'kept': 'keep', 'keeping': 'keep', 'keeps': 'keep',
  'held': 'hold', 'holding': 'hold', 'holds': 'hold',
  'wrote': 'write', 'written': 'write', 'writing': 'write', 'writes': 'write',
  'stood': 'stand', 'standing': 'stand', 'stands': 'stand',
  'heard': 'hear', 'hearing': 'hear', 'hears': 'hear',
  'let': 'let', 'letting': 'let', 'lets': 'let',
  'meant': 'mean', 'meaning': 'mean', 'means': 'mean',
  'became': 'become', 'becoming': 'become', 'becomes': 'become',
  'shown': 'show', 'showed': 'show', 'showing': 'show', 'shows': 'show',
  'ran': 'run', 'running': 'run', 'runs': 'run',
  'led': 'lead', 'leading': 'lead', 'leads': 'lead',
  'read': 'read', 'reading': 'read', 'reads': 'read',
  'set': 'set', 'setting': 'set', 'sets': 'set',
  'spent': 'spend', 'spending': 'spend', 'spends': 'spend',
  'lost': 'lose', 'losing': 'lose', 'loses': 'lose',
  'paid': 'pay', 'paying': 'pay', 'pays': 'pay',
  'met': 'meet', 'meeting': 'meet', 'meets': 'meet',
  'built': 'build', 'building': 'build', 'builds': 'build',
  'told': 'tell', 'telling': 'tell', 'tells': 'tell',
  'felt': 'feel', 'feeling': 'feel', 'feels': 'feel',
  'brought': 'bring', 'bringing': 'bring', 'brings': 'bring',
}

// 不规则名词复数映射
const IRREGULAR_NOUNS: Record<string, string> = {
  'children': 'child', 'mice': 'mouse', 'men': 'man', 'women': 'woman',
  'feet': 'foot', 'teeth': 'tooth', 'geese': 'goose',
  'people': 'person', 'phenomena': 'phenomenon', 'data': 'datum',
  'analyses': 'analysis', 'bases': 'basis', 'crises': 'crisis',
  'criteria': 'criterion', 'formulae': 'formula',
  'indices': 'index', 'matrices': 'matrix', 'stimuli': 'stimulus',
}

/**
 * 将单词还原为原型
 */
export function getBaseForm(word: string): string {
  const lower = word.toLowerCase().trim()
  
  // 空词或太短的词不处理
  if (!lower || lower.length <= 2) return lower
  
  // 先检查不规则动词
  if (IRREGULAR_VERBS[lower]) {
    return IRREGULAR_VERBS[lower]
  }
  
  // 检查不规则名词复数
  if (IRREGULAR_NOUNS[lower]) {
    return IRREGULAR_NOUNS[lower]
  }
  
  // 规则还原：按优先级尝试
  // 1. -ying → -ie (dying → die)
  if (lower.endsWith('ying') && lower.length > 4) {
    return lower.slice(0, -4) + 'ie'
  }
  
  // 2. -ied → -y (studied → study)
  if (lower.endsWith('ied') && lower.length > 3) {
    return lower.slice(0, -3) + 'y'
  }
  
  // 3. -ies → -y (flies → fly)
  if (lower.endsWith('ies') && lower.length > 3) {
    return lower.slice(0, -3) + 'y'
  }
  
  // 4. -ves → -f/-fe (knives → knife)
  if (lower.endsWith('ves') && lower.length > 3) {
    return lower.slice(0, -3) + 'fe'
  }
  
  // 5. -es → -e/-∅ (makes → make, boxes → box)
  if (lower.endsWith('es') && lower.length > 3) {
    // 特殊：以-ch, -sh, -ss, -x, -z结尾加-es
    if (lower.endsWith('ches') || lower.endsWith('shes') || lower.endsWith('sses') || lower.endsWith('xes') || lower.endsWith('zes')) {
      return lower.slice(0, -2)
    }
    // 其他情况直接去掉-s
    return lower.slice(0, -1)
  }
  
  // 6. -s → -∅ (runs → run)
  if (lower.endsWith('s') && !lower.endsWith('ss') && lower.length > 3) {
    return lower.slice(0, -1)
  }
  
  // 7. -ed → -∅/-e (played → play, moved → move)
  if (lower.endsWith('ed') && lower.length > 3) {
    // 以-ted, -ded结尾的直接去掉ed
    if (lower.endsWith('ted') || lower.endsWith('ded')) {
      return lower.slice(0, -2)
    }
    // 以e结尾的只加d (moved → move)
    if (lower.endsWith('ed') && lower.length > 3) {
      const base = lower.slice(0, -2)
      // 如果去掉ed后以e结尾，可能是原形
      if (base.endsWith('e')) return base
      // 否则尝试加e (move)
      if (lower.endsWith('ved') || lower.endsWith('zed') || lower.endsWith('sed')) {
        return lower.slice(0, -2) + 'e'
      }
      return base
    }
  }
  
  // 8. -ing → -∅/-e (running → run, making → make)
  if (lower.endsWith('ing') && lower.length > 4) {
    const base = lower.slice(0, -3)
    // 如果去掉ing后以e结尾，可能是原形
    if (base.endsWith('e')) return base
    // 双写辅音+ing → 单辅音 (running → run)
    if (base.length >= 2 && base[base.length - 1] === base[base.length - 2]) {
      return base.slice(0, -1)
    }
    // 以ve, ze, se结尾加ing的，去掉ing加e
    if (lower.endsWith('ving') || lower.endsWith('zing') || lower.endsWith('sing')) {
      return base + 'e'
    }
    return base
  }
  
  // 9. -ly → -∅ (quickly → quick)
  if (lower.endsWith('ly') && lower.length > 3) {
    return lower.slice(0, -2)
  }
  
  // 10. -er → -∅ (bigger → big)
  if (lower.endsWith('er') && lower.length > 3) {
    const base = lower.slice(0, -2)
    // 双写辅音+er → 单辅音
    if (base.length >= 2 && base[base.length - 1] === base[base.length - 2]) {
      return base.slice(0, -1)
    }
    return base
  }
  
  // 11. -est → -∅ (biggest → big)
  if (lower.endsWith('est') && lower.length > 4) {
    const base = lower.slice(0, -3)
    // 双写辅音+est → 单辅音
    if (base.length >= 2 && base[base.length - 1] === base[base.length - 2]) {
      return base.slice(0, -1)
    }
    return base
  }
  
  // 12. -tion → -∅ (education → educat)
  // 这个不太准确，先不处理
  
  // 13. -ment → -∅ (development → develop)
  if (lower.endsWith('ment') && lower.length > 5) {
    return lower.slice(0, -4)
  }
  
  // 14. -ness → -∅ (happiness → happy)
  if (lower.endsWith('ness') && lower.length > 5) {
    return lower.slice(0, -4)
  }
  
  // 15. -ful → -∅ (beautiful → beauti)
  // 这个不太准确，先不处理
  
  // 16. -less → -∅ (endless → end)
  if (lower.endsWith('less') && lower.length > 5) {
    return lower.slice(0, -4)
  }
  
  return lower
}
