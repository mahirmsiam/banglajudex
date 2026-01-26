import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Header from './components/Header'
import CaseDetailPage from './pages/CaseDetailPage'
import SearchPage from './pages/SearchPage'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/case/:caseId" element={<CaseDetailPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
