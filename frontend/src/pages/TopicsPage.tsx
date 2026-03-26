import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { DatePicker } from '../components/DatePicker'
import { TopicCard } from '../components/TopicCard'

export function TopicsPage() {
  const today = new Date().toISOString().split('T')[0]
  const [selectedDate, setSelectedDate] = useState(today)
  const [showBlindSpotOnly, setShowBlindSpotOnly] = useState(false)

  const { data: topics = [], isLoading } = useQuery({
    queryKey: ['topics', selectedDate],
    queryFn: () => api.getTopics(selectedDate),
  })

  const filtered = showBlindSpotOnly ? topics.filter(t => t.is_blind_spot) : topics

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <DatePicker value={selectedDate} onChange={setSelectedDate} />
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={showBlindSpotOnly}
            onChange={e => setShowBlindSpotOnly(e.target.checked)}
            className="rounded"
          />
          只看盲区话题
        </label>
      </div>

      {isLoading && <p className="text-gray-500 text-sm">加载中...</p>}

      {!isLoading && filtered.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🗂️</p>
          <p>{selectedDate} 暂无主题数据</p>
        </div>
      )}

      <div className="space-y-3">
        {filtered.map(topic => (
          <TopicCard key={topic.id} topic={topic} />
        ))}
      </div>
    </div>
  )
}
