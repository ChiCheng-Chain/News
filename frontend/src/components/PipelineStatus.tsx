import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const STEP_LABELS: Record<string, string> = {
  collect: '采集新闻',
  deduplicate: '去重过滤',
  analyze: '分析视角',
  aggregate: '聚合事件',
  summarize: '生成简报',
  done: '完成',
}

export function PipelineStatus() {
  const { data } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: api.getPipelineStatus,
    refetchInterval: (query) =>
      query.state.data?.status === 'running' ? 3000 : false,
  })

  if (!data || data.status === 'idle' || data.status === 'done') return null

  if (data.status === 'failed') {
    return (
      <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
        Pipeline 运行失败：{data.error_msg}
      </div>
    )
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-700 flex items-center gap-2">
      <span className="animate-spin">⏳</span>
      正在运行：{STEP_LABELS[data.current_step ?? ''] ?? data.current_step}
    </div>
  )
}
