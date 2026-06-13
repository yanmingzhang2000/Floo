/**
 * 跨端存储适配
 *
 * 为什么要封装：H5 用 localStorage，小程序只能用 uni.getStorageSync。
 * 统一一个 API 出去，业务层就不用判断平台了。
 */

export const storage = {
  get(key: string): string | null {
    try {
      const value = uni.getStorageSync(key)
      // uni.getStorageSync 在小程序里查不到时返回 ''，统一成 null
      return value === '' || value === undefined ? null : String(value)
    } catch (e) {
      console.warn('storage.get failed:', key, e)
      return null
    }
  },

  set(key: string, value: string | number): void {
    try {
      uni.setStorageSync(key, String(value))
    } catch (e) {
      console.warn('storage.set failed:', key, e)
    }
  },

  remove(key: string): void {
    try {
      uni.removeStorageSync(key)
    } catch (e) {
      console.warn('storage.remove failed:', key, e)
    }
  },

  /** 取数字，找不到或解析失败返回 null */
  getNumber(key: string): number | null {
    const v = storage.get(key)
    if (v === null) return null
    const n = Number(v)
    return Number.isFinite(n) ? n : null
  },

  /** 取 JSON 对象，解析失败返回 null */
  getJSON<T = unknown>(key: string): T | null {
    const v = storage.get(key)
    if (v === null) return null
    try {
      return JSON.parse(v) as T
    } catch {
      return null
    }
  },

  setJSON(key: string, obj: unknown): void {
    storage.set(key, JSON.stringify(obj))
  },
}