import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from './App'

// Mock fetch globally
global.fetch = vi.fn()

describe('App Component', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the main heading', async () => {
    // Mock the initial history fetch (even if not in history view, let's satisfy any potential calls)
    fetch.mockResolvedValue({
      ok: true,
      json: async () => []
    })

    render(<App />)
    
    expect(screen.getByText(/What's your audience/i)).toBeInTheDocument()
    expect(screen.getByText(/Generate Weekly Pulse/i)).toBeInTheDocument()
  })

  it('shows the history view when the button is clicked', async () => {
    // Mock history fetch
    fetch.mockResolvedValue({
      ok: true,
      json: async () => [
        { id: 1, report_name: 'Test Report', source: 'Play Store', review_count: 200, generated_at: '2026-03-24' }
      ]
    })

    render(<App />)
    
    const historyButton = screen.getByRole('button', { name: /Past Reports/i })
    await user.click(historyButton)

    // Wait for history to load
    const reportName = await screen.findByText(/Test Report/i)
    expect(reportName).toBeInTheDocument()
  })
})
