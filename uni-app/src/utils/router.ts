/**
 * 路由跳转适配层
 *
 * 为什么要封装：tabBar 页要用 switchTab，普通页要用 navigateTo，写法不统一。
 * 这里根据 tabBar 页面表自动选对的 API。
 */

// tabBar 页面列表（必须和 pages.json 里的 tabBar 配置保持一致）
const TAB_PAGES = [
  '/pages/learning/index',
  '/pages/dictionary/index',
  '/pages/review/index',
  '/pages/checkin/index',
]

function isTabPage(path: string): boolean {
  // 去掉 query 部分再判断
  const pure = path.split('?')[0]
  return TAB_PAGES.includes(pure)
}

/**
 * 跳转到指定页面，自动判断 tab/普通页
 */
export function navTo(path: string) {
  if (!path.startsWith('/')) path = '/' + path
  if (isTabPage(path)) {
    uni.switchTab({ url: path.split('?')[0] })
    return
  }
  uni.navigateTo({ url: path })
}

/**
 * 替换当前页
 */
export function navReplace(path: string) {
  if (!path.startsWith('/')) path = '/' + path
  if (isTabPage(path)) {
    uni.switchTab({ url: path.split('?')[0] })
    return
  }
  uni.redirectTo({ url: path })
}

/**
 * 重新启动到某页（清空栈）
 */
export function navReLaunch(path: string) {
  if (!path.startsWith('/')) path = '/' + path
  uni.reLaunch({ url: path })
}

/**
 * 返回上一页
 */
export function navBack(delta = 1) {
  uni.navigateBack({ delta })
}

/**
 * 解析当前页面 query
 */
export function getQuery(): Record<string, string> {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as any
  if (!current) return {}
  return current.options || current.$page?.options || {}
}