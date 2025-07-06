/**
 * API 工具函数 - 统一处理后端响应格式
 */

import { AxiosResponse } from 'axios'

/**
 * 从后端响应中提取数据
 * 处理两种格式：
 * 1. 直接返回数据数组或对象
 * 2. StandardResponse 格式 { success: true, data: {...} }
 */
export function extractData<T = any>(response: AxiosResponse): T {
  const responseData = response.data
  
  // 检查是否是 StandardResponse 格式
  if (responseData && typeof responseData === 'object' && 'success' in responseData) {
    // StandardResponse 格式
    if ('data' in responseData) {
      return responseData.data
    }
    // 某些情况下数据可能直接在响应中
    const { success, code, message, timestamp, request_id, ...rest } = responseData
    return rest as T
  }
  
  // 直接返回的数据
  return responseData
}

/**
 * 处理分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    total: number
    page: number
    page_size: number
    total_pages: number
    has_next?: boolean
    has_prev?: boolean
  }
}

export function extractPaginatedData<T = any>(response: AxiosResponse): PaginatedResponse<T> {
  const data = extractData(response)
  
  // 检查是否有特定的数据字段（如 courses, users 等）
  const keys = Object.keys(data)
  const dataKey = keys.find(key => Array.isArray(data[key]) && key !== 'pagination')
  
  if (dataKey && data.pagination) {
    return {
      items: data[dataKey],
      pagination: data.pagination
    }
  }
  
  // 如果没有分页信息，返回默认结构
  if (Array.isArray(data)) {
    return {
      items: data,
      pagination: {
        total: data.length,
        page: 1,
        page_size: data.length,
        total_pages: 1
      }
    }
  }
  
  throw new Error('Invalid paginated response format')
}