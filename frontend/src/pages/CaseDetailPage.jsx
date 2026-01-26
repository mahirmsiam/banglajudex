import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCase } from '../services/api'

function CaseDetailPage() {
  const { caseId } = useParams()
  const [caseData, setCaseData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadCase()
  }, [caseId])

  const loadCase = async () => {
    try {
      const data = await getCase(caseId)
      setCaseData(data)
    } catch (err) {
      console.error('Failed to load case:', err)
      setError('Failed to load case details.')
    } finally {
      setIsLoading(false)
    }
  }

  const formatCourt = (court) => {
    return court.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (isLoading) {
    return (
      <div style={{ width: '100%' }}>
        <div className="skeleton" style={{ height: '40px', width: '200px', marginBottom: '24px' }}></div>
        <div className="skeleton" style={{ height: '60px', width: '80%', marginBottom: '16px' }}></div>
        <div className="skeleton" style={{ height: '200px', width: '100%' }}></div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ width: '100%' }}>
        <div className="error-banner">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
        <Link to="/" style={{ 
          color: 'var(--accent-primary)', 
          marginTop: '16px', 
          display: 'inline-block' 
        }}>
          ← Back to Search
        </Link>
      </div>
    )
  }

  return (
    <div style={{ width: '100%' }}>
      {/* Back Link */}
      <Link to="/" style={{ 
        color: 'var(--accent-primary)', 
        marginBottom: '24px', 
        display: 'inline-block',
        textDecoration: 'none',
        fontSize: '0.875rem'
      }}>
        ← Back to Search
      </Link>

      {/* Case Header */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-primary)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-xl)',
        marginBottom: 'var(--spacing-xl)'
      }}>
        <div style={{ display: 'flex', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
          <span className="result-card__court">{formatCourt(caseData.court)}</span>
          {caseData.case_type && (
            <span style={{
              fontSize: '0.75rem',
              padding: '2px 8px',
              background: 'var(--bg-tertiary)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-secondary)'
            }}>
              {caseData.case_type.replace(/_/g, ' ').toUpperCase()}
            </span>
          )}
          {caseData.outcome && (
            <span style={{
              fontSize: '0.75rem',
              padding: '2px 8px',
              background: caseData.outcome === 'allowed' ? 'rgba(45, 212, 191, 0.1)' : 'var(--bg-tertiary)',
              color: caseData.outcome === 'allowed' ? 'var(--success)' : 'var(--text-secondary)',
              borderRadius: 'var(--radius-sm)'
            }}>
              {caseData.outcome.toUpperCase()}
            </span>
          )}
        </div>

        <h1 style={{
          fontFamily: 'var(--font-serif)',
          fontSize: '1.75rem',
          fontWeight: '600',
          marginBottom: 'var(--spacing-sm)',
          color: 'var(--text-primary)'
        }}>
          {caseData.case_title}
        </h1>

        <p style={{
          color: 'var(--accent-secondary)',
          fontSize: '1rem',
          marginBottom: 'var(--spacing-lg)'
        }}>
          {caseData.case_number}
        </p>

        {/* Metadata Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: 'var(--spacing-md)'
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
              Judgment Date
            </span>
            <p style={{ color: 'var(--text-primary)', marginTop: '4px' }}>
              {formatDate(caseData.judgment_date)}
            </p>
          </div>

          {caseData.judges && caseData.judges.length > 0 && (
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                Bench
              </span>
              <p style={{ color: 'var(--text-primary)', marginTop: '4px' }}>
                {caseData.judges.map(j => j.name).join(', ')}
              </p>
            </div>
          )}

          {caseData.crime_category && (
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                Crime Category
              </span>
              <p style={{ color: 'var(--text-primary)', marginTop: '4px' }}>
                {caseData.crime_category}
              </p>
            </div>
          )}
        </div>

        {/* Statutes */}
        {caseData.statutes && caseData.statutes.length > 0 && (
          <div style={{ marginTop: 'var(--spacing-lg)' }}>
            <span style={{ 
              color: 'var(--text-muted)', 
              fontSize: '0.75rem', 
              textTransform: 'uppercase',
              display: 'block',
              marginBottom: '8px'
            }}>
              Statutes Cited
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {caseData.statutes.map((statute, idx) => (
                <span key={idx} style={{
                  padding: '4px 12px',
                  background: 'var(--accent-glow)',
                  border: '1px solid var(--border-accent)',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.8125rem',
                  color: 'var(--accent-secondary)'
                }}>
                  {statute.section ? `Section ${statute.section} of ` : ''}{statute.statute_name}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Paragraphs */}
      <h2 style={{
        fontSize: '1.125rem',
        fontWeight: '600',
        marginBottom: 'var(--spacing-md)',
        color: 'var(--text-primary)'
      }}>
        Judgment Text ({caseData.paragraphs?.length || 0} paragraphs)
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
        {caseData.paragraphs?.map((para, idx) => (
          <div 
            key={para.id} 
            id={`para-${para.para_no}`}
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--spacing-lg)'
            }}
          >
            <div style={{
              display: 'flex',
              gap: 'var(--spacing-sm)',
              marginBottom: 'var(--spacing-sm)',
              fontSize: '0.75rem',
              color: 'var(--text-muted)'
            }}>
              <span>📄 Page {para.page_no}</span>
              <span>•</span>
              <span>¶ {para.para_no}</span>
              {para.section_heading && para.section_heading !== 'unknown' && (
                <>
                  <span>•</span>
                  <span style={{ color: 'var(--accent-primary)' }}>
                    {para.section_heading.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </>
              )}
            </div>
            <p style={{
              color: 'var(--text-secondary)',
              lineHeight: '1.8',
              fontSize: '0.9375rem'
            }}>
              {para.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default CaseDetailPage
