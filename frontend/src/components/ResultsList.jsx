import { Link } from 'react-router-dom'

function ResultCard({ result }) {
  const { citation, text, score, section_heading, case_id } = result

  const formatCourt = (court) => {
    return court.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatSection = (section) => {
    if (!section) return null
    return section.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const highlightText = (text, maxLength = 400) => {
    const truncated = text.length > maxLength 
      ? text.substring(0, maxLength) + '...' 
      : text
    return truncated
  }

  return (
    <Link to={`/case/${case_id}`} className="result-card" style={{ textDecoration: 'none' }}>
      <div className="result-card__citation">
        <span className="result-card__court">{formatCourt(citation.court)}</span>
        <span className="result-card__location">
          📄 Page {citation.page_no}, Para {citation.para_no}
        </span>
        {section_heading && section_heading !== 'unknown' && (
          <span className="result-card__location">
            | {formatSection(section_heading)}
          </span>
        )}
      </div>
      
      <h3 className="result-card__title">{citation.case_title}</h3>
      <p className="result-card__case-number">{citation.case_number}</p>
      <p className="result-card__text">{highlightText(text)}</p>
      
      <div className="result-card__score">
        <div className="result-card__score-bar">
          <div 
            className="result-card__score-fill" 
            style={{ width: `${Math.round(score * 100)}%` }}
          />
        </div>
        <span className="result-card__score-value">
          {Math.round(score * 100)}% match
        </span>
      </div>
    </Link>
  )
}

function ResultsList({ results, isLoading, query }) {
  if (isLoading) {
    return (
      <div className="results-list">
        {[1, 2, 3].map((i) => (
          <div key={i} className="result-card">
            <div className="skeleton" style={{ height: '20px', width: '150px', marginBottom: '12px' }}></div>
            <div className="skeleton" style={{ height: '24px', width: '80%', marginBottom: '8px' }}></div>
            <div className="skeleton" style={{ height: '16px', width: '40%', marginBottom: '16px' }}></div>
            <div className="skeleton" style={{ height: '80px', width: '100%' }}></div>
          </div>
        ))}
      </div>
    )
  }

  if (!query) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">⚖️</div>
        <h3 className="empty-state__title">Search Bangladesh Supreme Court Judgments</h3>
        <p className="empty-state__description">
          Enter a legal question or search term to find relevant paragraphs from 
          Appellate Division and High Court Division judgments with page-level citations.
        </p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">📭</div>
        <h3 className="empty-state__title">No Results Found</h3>
        <p className="empty-state__description">
          No explicit finding on this issue was located in the uploaded judgments.
          Try adjusting your search terms or filters.
        </p>
      </div>
    )
  }

  return (
    <div className="results-list">
      <div className="results-header">
        <span className="results-count">
          Found <span>{results.length}</span> relevant paragraphs
        </span>
      </div>
      
      {results.map((result) => (
        <ResultCard key={result.paragraph_id} result={result} />
      ))}
    </div>
  )
}

export default ResultsList
