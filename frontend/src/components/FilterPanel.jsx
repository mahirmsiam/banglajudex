import { useEffect, useState } from 'react'
import { getFilterOptions } from '../services/api'

function FilterPanel({ filters, onFilterChange, onClear }) {
  const [options, setOptions] = useState({
    courts: [],
    years: [],
    judges: [],
    case_types: [],
    outcomes: [],
    statutes: [],
    crime_categories: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadFilterOptions()
  }, [])

  const loadFilterOptions = async () => {
    try {
      const data = await getFilterOptions()
      setOptions(data)
    } catch (error) {
      console.error('Failed to load filter options:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (key, value) => {
    onFilterChange({
      ...filters,
      [key]: value || null
    })
  }

  if (loading) {
    return (
      <aside className="filter-panel">
        <div className="filter-card">
          <div className="skeleton" style={{ height: '200px' }}></div>
        </div>
      </aside>
    )
  }

  return (
    <aside className="filter-panel">
      <div className="filter-card">
        <h2 className="filter-card__title">
          <span>🔧</span> Filters
        </h2>

        {/* Court Filter */}
        <div className="filter-group">
          <label className="filter-group__label">Court</label>
          <select
            className="filter-group__select"
            value={filters.court || ''}
            onChange={(e) => handleChange('court', e.target.value)}
          >
            <option value="">All Courts</option>
            {options.courts.map((court) => (
              <option key={court} value={court}>
                {court.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
        </div>

        {/* Year Range */}
        <div className="filter-group">
          <label className="filter-group__label">Year From</label>
          <select
            className="filter-group__select"
            value={filters.year_from || ''}
            onChange={(e) => handleChange('year_from', e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">Any Year</option>
            {options.years.map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-group__label">Year To</label>
          <select
            className="filter-group__select"
            value={filters.year_to || ''}
            onChange={(e) => handleChange('year_to', e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">Any Year</option>
            {options.years.map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>

        {/* Case Type */}
        <div className="filter-group">
          <label className="filter-group__label">Case Type</label>
          <select
            className="filter-group__select"
            value={filters.case_type || ''}
            onChange={(e) => handleChange('case_type', e.target.value)}
          >
            <option value="">All Types</option>
            {options.case_types.map((type) => (
              <option key={type} value={type}>
                {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
        </div>

        {/* Outcome */}
        <div className="filter-group">
          <label className="filter-group__label">Outcome</label>
          <select
            className="filter-group__select"
            value={filters.outcome || ''}
            onChange={(e) => handleChange('outcome', e.target.value)}
          >
            <option value="">All Outcomes</option>
            {options.outcomes.map((outcome) => (
              <option key={outcome} value={outcome}>
                {outcome.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
        </div>

        {/* Statute */}
        <div className="filter-group">
          <label className="filter-group__label">Statute</label>
          <select
            className="filter-group__select"
            value={filters.statute_name || ''}
            onChange={(e) => handleChange('statute_name', e.target.value)}
          >
            <option value="">All Statutes</option>
            {options.statutes.slice(0, 50).map((statute) => (
              <option key={statute} value={statute}>
                {statute.length > 40 ? statute.substring(0, 40) + '...' : statute}
              </option>
            ))}
          </select>
        </div>

        {/* Section */}
        <div className="filter-group">
          <label className="filter-group__label">Section</label>
          <input
            type="text"
            className="filter-group__input"
            placeholder="e.g., 96"
            value={filters.section || ''}
            onChange={(e) => handleChange('section', e.target.value)}
          />
        </div>

        {/* Judge */}
        <div className="filter-group">
          <label className="filter-group__label">Judge</label>
          <select
            className="filter-group__select"
            value={filters.judge || ''}
            onChange={(e) => handleChange('judge', e.target.value)}
          >
            <option value="">All Judges</option>
            {options.judges.slice(0, 50).map((judge) => (
              <option key={judge} value={judge}>{judge}</option>
            ))}
          </select>
        </div>

        {/* Clear Button */}
        <button className="filter-clear" onClick={onClear}>
          Clear All Filters
        </button>
      </div>
    </aside>
  )
}

export default FilterPanel
