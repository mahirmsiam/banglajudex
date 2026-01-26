import { useState } from 'react'
import ConversationView from '../components/ConversationView'
import FilterPanel from '../components/FilterPanel'
import ResultsList from '../components/ResultsList'
import SearchBar from '../components/SearchBar'
import { searchJudgments } from '../services/api'

function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [filters, setFilters] = useState({})
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('search') // 'search' or 'conversation'

  const handleSearch = async (searchQuery) => {
    setQuery(searchQuery)
    setIsLoading(true)
    setError(null)

    try {
      const response = await searchJudgments(searchQuery, filters)
      setResults(response.results)
    } catch (err) {
      console.error('Search failed:', err)
      setError('Failed to search. Please check your connection and try again.')
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
    // Re-search with new filters if there's an active query
    if (query) {
      handleSearch(query)
    }
  }

  const handleClearFilters = () => {
    setFilters({})
    if (query) {
      handleSearch(query)
    }
  }

  return (
    <>
      <div className="search-section">
        {/* Tab Switcher */}
        <div style={{ 
          display: 'flex', 
          gap: 'var(--spacing-sm)', 
          marginBottom: 'var(--spacing-md)' 
        }}>
          <button
            onClick={() => setActiveTab('search')}
            style={{
              padding: 'var(--spacing-sm) var(--spacing-lg)',
              background: activeTab === 'search' ? 'var(--accent-primary)' : 'var(--bg-card)',
              border: '1px solid ' + (activeTab === 'search' ? 'var(--accent-primary)' : 'var(--border-primary)'),
              borderRadius: 'var(--radius-md)',
              color: activeTab === 'search' ? 'var(--bg-primary)' : 'var(--text-secondary)',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
          >
            🔍 Search
          </button>
          <button
            onClick={() => setActiveTab('conversation')}
            style={{
              padding: 'var(--spacing-sm) var(--spacing-lg)',
              background: activeTab === 'conversation' ? 'var(--accent-primary)' : 'var(--bg-card)',
              border: '1px solid ' + (activeTab === 'conversation' ? 'var(--accent-primary)' : 'var(--border-primary)'),
              borderRadius: 'var(--radius-md)',
              color: activeTab === 'conversation' ? 'var(--bg-primary)' : 'var(--text-secondary)',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
          >
            💬 Conversation
          </button>
        </div>

        {activeTab === 'search' ? (
          <>
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            
            {error && (
              <div className="error-banner">
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <ResultsList 
              results={results} 
              isLoading={isLoading} 
              query={query} 
            />
          </>
        ) : (
          <div style={{ 
            flex: 1, 
            background: 'var(--bg-card)', 
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-primary)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            minHeight: '500px'
          }}>
            <ConversationView filters={filters} />
          </div>
        )}
      </div>

      <FilterPanel 
        filters={filters}
        onFilterChange={handleFilterChange}
        onClear={handleClearFilters}
      />
    </>
  )
}

export default SearchPage
