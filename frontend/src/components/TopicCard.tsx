import { useState } from 'react'
import type { Topic } from '../api/client'

interface TopicCardProps {
  topic: Topic
}

export function TopicCard({ topic }: TopicCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {topic.is_blind_spot && (
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">盲区</span>
            )}
            <h3 className="font-medium text-gray-900">{topic.title}</h3>
          </div>
          <p className="text-sm text-gray-600">{topic.summary}</p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-500 hover:underline whitespace-nowrap"
        >
          {expanded ? '收起' : `查看 ${topic.perspectives?.length ?? 0} 个视角`}
        </button>
      </div>

      {expanded && topic.perspectives?.length > 0 && (
        <div className="mt-3 space-y-2 border-t pt-3">
          {topic.perspectives.map((p, i) => (
            <div key={i} className="bg-gray-50 rounded p-3">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-gray-500">{p.source}</span>
                <span className="text-xs text-gray-400">·</span>
                <span className="text-xs text-gray-500">{p.stance}</span>
              </div>
              <p className="text-sm text-gray-700">{p.summary}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
