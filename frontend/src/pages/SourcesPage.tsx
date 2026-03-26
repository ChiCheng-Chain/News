import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export function SourcesPage() {
  const queryClient = useQueryClient()

  const { data: sources = [], isLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: api.getSources,
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      api.updateSource(id, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-lg font-semibold text-gray-900 mb-4">新闻来源管理</h1>

      {isLoading && <p className="text-gray-500 text-sm">加载中...</p>}

      <div className="space-y-2">
        {sources.map(source => (
          <div
            key={source.id}
            className="flex items-center justify-between border border-gray-200 rounded-lg px-4 py-3"
          >
            <div>
              <p className="font-medium text-sm text-gray-900">{source.name}</p>
              <p className="text-xs text-gray-400">
                {source.type.toUpperCase()} · {source.language}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={source.enabled}
                onChange={e =>
                  toggleMutation.mutate({ id: source.id, enabled: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-10 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:bg-blue-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-4" />
            </label>
          </div>
        ))}
      </div>
    </div>
  )
}
