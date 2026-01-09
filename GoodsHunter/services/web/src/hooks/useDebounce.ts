/**
 * 防抖 Hook
 * 
 * 用于延迟执行函数，常用于搜索输入等场景。
 */

import { useEffect, useRef, useCallback } from 'react'

/**
 * 防抖 Hook
 * 
 * @param callback 要防抖的回调函数
 * @param delay 延迟时间（毫秒）
 * @param deps 依赖数组（当依赖变化时，会重新创建防抖函数）
 * 
 * @example
 * ```tsx
 * const debouncedSearch = useDebounce((query: string) => {
 *   updateState({ q: query })
 * }, 300, [updateState])
 * 
 * <input onChange={(e) => debouncedSearch(e.target.value)} />
 * ```
 */
export function useDebounce<T extends (...args: any[]) => void>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const callbackRef = useRef(callback)

  // 更新回调引用
  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  // 清理函数
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  const debouncedCallback = useCallback(
    ((...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = setTimeout(() => {
        callbackRef.current(...args)
      }, delay)
    }) as T,
    [delay, ...deps]
  )

  return debouncedCallback
}
