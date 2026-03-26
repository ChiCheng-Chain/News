import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import { api } from '../api/client'
import { DatePicker } from '../components/DatePicker'
import { PipelineStatus } from '../components/PipelineStatus'

export function DigestPage() {
  const today = new Date().toISOString().split('T')[0]
  const [selectedDate, setSelectedDate] = useState(today)
  const queryClient = useQueryClient()

  const { data: digest, isLoading, isError } = useQuery({
    queryKey: ['digest', selectedDate],
    queryFn: () => api.getDigest(selectedDate),
    retry: false,
  })

  const triggerMutation = useMutation({
    mutationFn: api.triggerPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-status'] })
    },
  })

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <DatePicker value={selectedDate} onChange={setSelectedDate} />
        {selectedDate === today && (
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={triggerMutation.isPending}
            className="text-sm bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {triggerMutation.isPending ? '启动中...' : '立即刷新'}
          </button>
        )}
      </div>

      <PipelineStatus />

      {triggerMutation.isError && (
        <div className="my-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
          {(triggerMutation.error as any)?.response?.data?.detail ?? '触发失败，请稍后重试'}
        </div>
      )}

      <div className="mt-4">
        {isLoading && <p className="text-gray-500 text-sm">加载中...</p>}
        {isError && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-3">📭</p>
            <p>{selectedDate} 暂无简报</p>
            {selectedDate === today && (
              <p className="text-sm mt-1">点击右上角「立即刷新」生成今日简报</p>
            )}
          </div>
        )}
        {digest && (
          <article className="prose prose-gray max-w-none">
            <ReactMarkdown>{digest.content}</ReactMarkdown>
          </article>
        )}
      </div>
    </div>
  )
}
