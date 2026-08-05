/**
 * copilotService.js — ForenSight AI Copilot
 * ==========================================
 * Handles SSE streaming and non-streaming requests to the Groq-powered
 * AI Investigation Copilot backend.
 */

import api from './api'

const API_BASE = '/api/v1'

/**
 * SSE Streaming copilot request.
 * Calls onToken(chunk) for each token, onSources(sources) once, onDone(confidence) at end.
 * Returns AbortController so the caller can stop generation.
 *
 * @param {string}   caseId
 * @param {string}   question
 * @param {Array}    history   - Array of {role, content} messages
 * @param {Function} onToken   - Called with each string token chunk
 * @param {Function} onSources - Called once with sources array
 * @param {Function} onDone    - Called with confidence string on completion
 * @param {Function} onError   - Called with error message string
 * @returns {AbortController}
 */
export function streamCopilot(caseId, question, history = [], onToken, onSources, onDone, onError) {
  const controller = new AbortController()

  const historyParam = encodeURIComponent(JSON.stringify(history.slice(-10)))
  const questionParam = encodeURIComponent(question)
  const token = localStorage.getItem('token') || sessionStorage.getItem('token') || ''

  const url = `${API_BASE}/cases/${caseId}/copilot/stream?question=${questionParam}&history=${historyParam}`

  const run = async () => {
    try {
      const resp = await fetch(url, {
        method: 'GET',
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
          Accept: 'text/event-stream',
        },
        signal: controller.signal,
      })

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`)
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // last incomplete line stays in buffer

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || trimmed === 'data: [DONE]') continue
          if (!trimmed.startsWith('data:')) continue

          const jsonStr = trimmed.slice(5).trim()
          try {
            const event = JSON.parse(jsonStr)
            if (event.type === 'token' && event.content) {
              onToken?.(event.content)
            } else if (event.type === 'sources') {
              onSources?.(event.sources || [])
            } else if (event.type === 'done') {
              onDone?.(event.confidence || 'High')
            } else if (event.type === 'error') {
              onError?.(event.content || 'An error occurred.')
            }
          } catch {
            // Ignore malformed SSE lines
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        // User stopped generation — normal
        onDone?.('Stopped')
      } else {
        onError?.(err.message || 'Connection failed. Please try again.')
      }
    }
  }

  run()
  return controller
}

/**
 * Non-streaming copilot request (fallback for environments that don't support SSE).
 */
export async function askCopilot(caseId, question, history = []) {
  const res = await api.post(`/cases/${caseId}/copilot`, { question, history })
  return res.data
}

/**
 * Semantic event search.
 */
export async function searchEvents(caseId, query, limit = 10) {
  const res = await api.get(`/cases/${caseId}/search`, { params: { query, limit } })
  return res.data
}
