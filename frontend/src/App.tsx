import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NavBar } from './components/NavBar'
import { DigestPage } from './pages/DigestPage'
import { TopicsPage } from './pages/TopicsPage'
import { SourcesPage } from './pages/SourcesPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <NavBar />
          <main>
            <Routes>
              <Route path="/" element={<DigestPage />} />
              <Route path="/topics" element={<TopicsPage />} />
              <Route path="/sources" element={<SourcesPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
