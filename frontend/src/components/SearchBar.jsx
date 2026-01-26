import { useState } from 'react'

function SearchBar({ onSearch, isLoading }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim().length >= 3) {
      onSearch(query.trim())
    }
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <span className="search-bar__icon">🔍</span>
      <input
        type="text"
        className="search-bar__input"
        placeholder="Search judgments... e.g., 'Section 96 pre-emption after mutation'"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={isLoading}
        minLength={3}
        aria-label="Search query"
      />
      <button 
        type="submit" 
        className="search-bar__submit"
        disabled={isLoading || query.trim().length < 3}
      >
        {isLoading ? (
          <span className="loading-spinner"></span>
        ) : (
          'Search'
        )}
      </button>
    </form>
  )
}

export default SearchBar
