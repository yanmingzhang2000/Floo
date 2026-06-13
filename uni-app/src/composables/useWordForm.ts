/**
 * 词形还原工具
 * 将单词的各种变形还原为原型
 */

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

const IRREGULAR_NOUNS: Record<string, string> = {
  'children': 'child', 'mice': 'mouse', 'men': 'man', 'women': 'woman',
  'feet': 'foot', 'teeth': 'tooth', 'geese': 'goose',
  'people': 'person', 'phenomena': 'phenomenon', 'data': 'datum',
  'analyses': 'analysis', 'bases': 'basis', 'crises': 'crisis',
  'criteria': 'criterion', 'formulae': 'formula',
  'indices': 'index', 'matrices': 'matrix', 'stimuli': 'stimulus',
}

export function getBaseForm(word: string): string {
  const lower = word.toLowerCase().trim()
  if (!lower || lower.length <= 2) return lower
  if (IRREGULAR_VERBS[lower]) return IRREGULAR_VERBS[lower]
  if (IRREGULAR_NOUNS[lower]) return IRREGULAR_NOUNS[lower]

  if (lower.endsWith('ying') && lower.length > 4) {
    return lower.slice(0, -4) + 'ie'
  }
  if (lower.endsWith('ied') && lower.length > 3) {
    return lower.slice(0, -3) + 'y'
  }
  if (lower.endsWith('ies') && lower.length > 3) {
    return lower.slice(0, -3) + 'y'
  }
  if (lower.endsWith('ves') && lower.length > 4 && !lower.endsWith('oves')) {
    return lower.slice(0, -3) + 'fe'
  }
  if (lower.endsWith('es') && lower.length > 4) {
    if (lower.endsWith('ches') || lower.endsWith('shes') || lower.endsWith('sses') || lower.endsWith('xes') || lower.endsWith('zes')) {
      return lower.slice(0, -2)
    }
    if (lower.endsWith('tes') || lower.endsWith('des') || lower.endsWith('ses') || lower.endsWith('zes') || lower.endsWith('ces')) {
      return lower
    }
    return lower.slice(0, -1)
  }
  if (lower.endsWith('s') && !lower.endsWith('ss') && lower.length > 4) {
    if (lower.endsWith('ous') || lower.endsWith('is') || lower.endsWith('us') || lower.endsWith('as') || lower.endsWith('ex') || lower.endsWith('ix')) {
      return lower
    }
    return lower.slice(0, -1)
  }
  if (lower.endsWith('ed') && lower.length > 3) {
    if (lower.endsWith('ted') || lower.endsWith('ded')) {
      return lower.slice(0, -2)
    }
    if (lower.endsWith('ed') && lower.length > 3) {
      const base = lower.slice(0, -2)
      if (base.endsWith('e')) return base
      if (lower.endsWith('ved') || lower.endsWith('zed') || lower.endsWith('sed')) {
        return lower.slice(0, -2) + 'e'
      }
      return base
    }
  }
  if (lower.endsWith('ing') && lower.length > 4) {
    const base = lower.slice(0, -3)
    if (base.endsWith('e')) return base
    if (base.length >= 2 && base[base.length - 1] === base[base.length - 2]) {
      return base.slice(0, -1)
    }
    if (lower.endsWith('ving') || lower.endsWith('zing') || lower.endsWith('sing')) {
      return base + 'e'
    }
    return base
  }
  if (lower.endsWith('ly') && lower.length > 3) {
    return lower.slice(0, -2)
  }
  if (lower.endsWith('er') && lower.length > 3) {
    const base = lower.slice(0, -2)
    if (base.length >= 2 && base[base.length - 1] === base[base.length - 2]) {
      return base.slice(0, -1)
    }
    return base
  }
  if (lower.endsWith('est') && lower.length > 4) {
    const base = lower.slice(0, -3)
    if (base.length >= 2 && base[base.length - 1] === base[base.length - 2]) {
      return base.slice(0, -1)
    }
    return base
  }
  if (lower.endsWith('ment') && lower.length > 5) {
    return lower.slice(0, -4)
  }
  if (lower.endsWith('ness') && lower.length > 5) {
    return lower.slice(0, -4)
  }
  if (lower.endsWith('less') && lower.length > 5) {
    return lower.slice(0, -4)
  }
  return lower
}