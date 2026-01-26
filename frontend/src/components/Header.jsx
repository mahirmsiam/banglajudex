import { Link } from 'react-router-dom'

function Header() {
  return (
    <header className="app-header">
      <div className="app-header__inner">
        <Link to="/" className="app-logo">
          <div className="app-logo__icon">⚖️</div>
          <h1 className="app-logo__text">
            Bangla<span>Judex</span>
          </h1>
        </Link>
        <nav className="app-nav">
          <span style={{ 
            fontSize: '0.75rem', 
            color: 'var(--text-muted)', 
            textTransform: 'uppercase', 
            letterSpacing: '0.1em' 
          }}>
            Bangladesh Supreme Court Judgments
          </span>
        </nav>
      </div>
    </header>
  )
}

export default Header
