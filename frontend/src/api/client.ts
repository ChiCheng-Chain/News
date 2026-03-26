import axios from 'axios'

const http = axios.create({ baseURL: '/' })

export interface Digest {
  id: number
  date: string
  content: string
  triggered_by: string
  created_at: string
}

export interface Perspective {
  source: string
  stance: string
  summary: string
}

export interface Topic {
  id: number
  title: string
  summary: string
  perspectives: Perspective[]
  is_blind_spot: boolean
  date: string
}

export interface Source {
  id: number
  name: string
  type: string
  url: string
  language: string
  enabled: boolean
}

export interface PipelineStatus {
  status: 'idle' | 'running' | 'done' | 'failed'
  current_step: string | null
  started_at: string | null
  finished_at: string | null
  error_msg: string | null
}

export const api = {
  getDigest: (date?: string) =>
    http.get<Digest>('/api/digest', { params: date ? { date } : {} }).then(r => r.data),

  getTopics: (date?: string) =>
    http.get<Topic[]>('/api/topics', { params: date ? { date } : {} }).then(r => r.data),

  getTopic: (id: number) =>
    http.get<Topic>(`/api/topics/${id}`).then(r => r.data),

  triggerPipeline: () =>
    http.post('/api/trigger').then(r => r.data),

  getPipelineStatus: () =>
    http.get<PipelineStatus>('/api/pipeline/status').then(r => r.data),

  getSources: () =>
    http.get<Source[]>('/api/sources').then(r => r.data),

  updateSource: (id: number, enabled: boolean) =>
    http.put<Source>(`/api/sources/${id}`, { enabled }).then(r => r.data),
}
