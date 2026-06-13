/**
 * 网络请求适配层
 * 
 * 为什么要封装：axios 只能在 H5 跑，小程序必须用 uni.request。
 * 这里统一封装一个类 axios 的接口，内部根据平台自动切换。
 */

import { storage } from './storage'

const API_BASE = 'https://floo-production.up.railway.app'

interface RequestConfig {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  params?: Record<string, any>
  header?: Record<string, string>
  timeout?: number
}

interface Response<T = any> {
  data: T
  statusCode: number
  header: Record<string, string>
}

/**
 * 发起 HTTP 请求
 */
function request<T = any>(config: RequestConfig): Promise<Response<T>> {
  return new Promise((resolve, reject) => {
    const { url, method = 'GET', data, params, header = {}, timeout = 60000 } = config

    // 拼接完整 URL
    let fullUrl = url.startsWith('http') ? url : API_BASE + url

    // 添加 query 参数（包括 user_id）
    const userId = storage.get('user_id')
    const allParams = { ...params }
    if (userId) {
      allParams.user_id = userId
    }

    if (Object.keys(allParams).length > 0) {
      const query = Object.entries(allParams)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join('&')
      fullUrl += (fullUrl.includes('?') ? '&' : '?') + query
    }

    // 默认 Content-Type
    if (!header['Content-Type'] && !header['content-type']) {
      header['Content-Type'] = 'application/json'
    }

    uni.request({
      url: fullUrl,
      method,
      data,
      header,
      timeout,
      success: (res) => {
        resolve(res as Response<T>)
      },
      fail: (err) => {
        reject(err)
      },
    })
  })
}

/**
 * 创建带拦截器的 request 实例（类 axios 接口）
 */
export function createRequest() {
  return {
    get<T = any>(url: string, config?: Omit<RequestConfig, 'url' | 'method'>): Promise<Response<T>> {
      return request<T>({ ...config, url, method: 'GET' })
    },
    post<T = any>(url: string, data?: any, config?: Omit<RequestConfig, 'url' | 'method' | 'data'>): Promise<Response<T>> {
      return request<T>({ ...config, url, method: 'POST', data })
    },
    put<T = any>(url: string, data?: any, config?: Omit<RequestConfig, 'url' | 'method' | 'data'>): Promise<Response<T>> {
      return request<T>({ ...config, url, method: 'PUT', data })
    },
    delete<T = any>(url: string, config?: Omit<RequestConfig, 'url' | 'method'>): Promise<Response<T>> {
      return request<T>({ ...config, url, method: 'DELETE' })
    },
  }
}

export const api = createRequest()