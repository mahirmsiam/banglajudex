import { useEffect, useRef, useState } from 'react'
import { queryJudgments } from '../services/api'

function Message({ message }) {
  const { role, content, citations } = message

  return (
    <div className={`message message--${role}`}>
      <div className="message__content">
        {content}
      </div>
      
      {citations && citations.length > 0 && (
        <div className="message__citations">
          <strong style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Citations:
          </strong>
          {citations.map((citation, idx) => (
            <div key={idx} className="message__citation-item">
              {citation.case_title} ({citation.case_number}) - 
              Page {citation.page_no}, Para {citation.para_no}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ConversationView({ filters }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Build conversation history for context
      const conversationHistory = messages.map(m => ({
        role: m.role,
        content: m.content
      }))

      const response = await queryJudgments(
        input.trim(),
        filters,
        conversationHistory
      )

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations
      }
      
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Query failed:', error)
      const errorMessage = {
        role: 'assistant',
        content: 'An error occurred while processing your query. Please try again.',
        citations: []
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="conversation-view">
      <div className="conversation-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__icon">💬</div>
            <h3 className="empty-state__title">Start a Conversation</h3>
            <p className="empty-state__description">
              Ask legal questions about Bangladesh Supreme Court judgments. 
              Get extractive answers with page-level citations.
            </p>
          </div>
        ) : (
          messages.map((message, idx) => (
            <Message key={idx} message={message} />
          ))
        )}
        
        {isLoading && (
          <div className="message message--assistant">
            <div className="message__content">
              <span className="loading-spinner"></span>
              <span style={{ marginLeft: '8px' }}>Searching judgments...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="conversation-input">
        <form className="conversation-input__form" onSubmit={handleSubmit}>
          <textarea
            className="conversation-input__field"
            placeholder="Ask a legal question... e.g., 'What did the court hold regarding Section 96 pre-emption?'"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
            rows={2}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="conversation-input__submit"
            disabled={isLoading || input.trim().length < 3}
          >
            {isLoading ? '...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default ConversationView
